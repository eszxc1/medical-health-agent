# 导入fastmcp
import random
import smtplib
import sys
import os
from email.mime.text import MIMEText

import pymysql
import redis
from fastmcp import FastMCP
from neo4j import GraphDatabase


# ===== 健康模块导入 =====
# 为什么需要手动添加 sys.path？
# —— 直接运行 `python mymcp/MCPServer.py` 时，Python 默认将 mymcp/ 加入 sys.path，
#    而非 rag_server/。手动添加父目录后，才能导入 health.dao、common 等模块。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.MySQLUtil import execute_query  # 统一 MySQL 查询入口（替代直接 pymysql 连接）
from common.UserUtil import resolve_user_id  # email → user_id 解析
from common.DateUtil import parse_relative_date, get_current_date as get_today, get_weekday_cn  # ★ 时间标准化工具（get_current_date 加别名，避免与下方 MCP 工具同名冲突）
from common.config import env, required_env  # ★ 统一配置加载（.env 支持）
from common.LangfuseUtil import observe  # ★ Langfuse 全链路追踪装饰器
from health.dao import HealthProfileDao
from health.dao import UserAllergyDao
from health.dao import UserChronicDiseaseDao
from health.dao import UserMedicationDao
from health.dao import HealthPlanDao
from health.disease_aliases import is_disease_match, normalize_disease_name  # ★ Phase 2/4 疾病名模糊匹配

# 创建FastMCP实例
mcp = FastMCP()

# 统一 Redis 配置（从环境变量读取）
REDIS_CONFIG = {
    'host': env('REDIS_HOST', 'localhost'),
    'port': int(env('REDIS_PORT', '6379')),
    'db': int(env('REDIS_DB', '0')),
    'decode_responses': True,
    'protocol': 2,
}

# 2. Neo4j 配置 (请根据你的实际环境修改)
NEO4J_CONFIG = {
    'uri': env('NEO4J_URI', 'neo4j://127.0.0.1:7687'),
    'username': env('NEO4J_USERNAME', 'neo4j'),
    'password': required_env('NEO4J_PASSWORD'),
    'database': env('NEO4J_DATABASE', 'neo4j')
}
# 3. 初始化 Neo4j 驱动
neo4j_driver = GraphDatabase.driver(
    NEO4J_CONFIG['uri'],
    auth=(NEO4J_CONFIG['username'], NEO4J_CONFIG['password'])
)

# ============================================================
# 原有工具（登录 & 知识图谱）
# ============================================================

# 查询mysql数据库数据的工具
# ★ 设计说明：params 类型标注为 str 而非 tuple
#   原因：Agent 调用工具时传入的是字符串（如 "cc"），FastMCP 会校验类型。
#       如果标注为 tuple，Pydantic 会拒绝 Agent 传入的字符串参数。
#       因此在工具层接受 str，内部转换为 pymysql 需要的 tuple 格式。
# ★ Bug 修复 3: 移除直接 pymysql 连接，改用 common.MySQLUtil.execute_query
#   原因：保持与 DAO 层代码风格统一，复用连接管理逻辑，减少重复代码。
@mcp.tool(
    name="find_email",
    description="根据用户信息查询出对应的邮箱号信息",
)
async def find_email(sql: str, params: str = None) -> dict:
    # 安全检查：只允许 SELECT 查询，防止 Agent 生成危险的 DML 语句
    if not sql.strip().lower().startswith("select"):
        return {"result": "只可以执行查询语句，不可以执行增删改语句"}
    try:
        # ★ 类型转换：Agent 传入的 params 是字符串（如 "cc"），
        #    但 pymysql 的 execute(sql, params) 要求 params 为 tuple。
        #    将字符串包装为单元素元组：("cc",) → 正确的参数绑定
        query_params = (params,) if params else None
        result = execute_query(sql, query_params)
        return {"result": result}
    except Exception as e:
        return {"result": str(e)}


# 发送邮件工具
# ★ Bug 修复 2: Redis 连接使用 try/finally 包裹
#   原因：如果 r.set() 抛出异常（如 Redis 服务不可用），r.close() 不会被执行，
#        导致连接泄漏。try/finally 保证无论是否异常，连接都会被正确释放。
@mcp.tool(
    name="send_email",
    description="给指定的邮箱发送登录的验证码"
)
async def send_email(receiver: str) -> dict:
    # 生成 4 位随机验证码
    code = ""
    for i in range(4):
        code += str(int(random.random() * 10))

    sender = env('SMTP_SENDER', '2682408715@qq.com')
    password = required_env('SMTP_PASSWORD')
    subject = "登录验证码"
    content = f"您的登录验证码是：{code}，过期时间为60s。"

    message = MIMEText(content, _subtype="plain", _charset="utf-8")
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = subject

    smtp_server = env('SMTP_SERVER', 'smtp.qq.com')
    smtp_port = int(env('SMTP_PORT', '587'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())
        server.quit()

        # ★ 修复：try/finally 确保 Redis 连接正确关闭
        r = redis.Redis(**REDIS_CONFIG)
        try:
            r.set(receiver, code, ex=60)
        finally:
            r.close()

        return {"result": "发送成功"}
    except Exception as e:
        return {"result": str(e)}


# 验证验证码工具
# ★ Bug 修复 2: 同上，Redis 连接使用 try/finally 包裹
@mcp.tool(
    name="verify_code",
    description="验证用户输入的验证码是否正确"
)
async def verify_code(receiver: str, code: str) -> dict:
    r = redis.Redis(**REDIS_CONFIG)
    try:
        redis_code = r.get(receiver)
        if redis_code == code:
            return {"result": "验证成功"}
        return {"result": "验证失败"}
    except Exception as e:
        return {"result": f"Redis错误: {str(e)}"}
    finally:
        # ★ 修复：无论是否异常，都确保 Redis 连接被关闭
        r.close()


# 4. 定义 find_data 工具 (对应 Prompt 中的流程 B)
@observe(name="find_data", as_type="tool")
@mcp.tool(
    name="find_data",
    description="执行 Cypher 查询语句以检索 Neo4j 图数据库中的医疗知识。"
)
async def find_data(cypher: str, params: dict = None) -> dict:
    """
    执行 Cypher 查询并返回结果。
    参数:
        cypher (str): Cypher 查询语句 (MATCH ... RETURN ...)。
        params (dict, optional): 查询参数。
    返回:
        dict: 包含查询结果或错误信息。
    """
    # 安全检查：只允许读取操作
    safe_keywords = ["MATCH", "RETURN", "WHERE", "ORDER", "LIMIT"]
    if not any(cypher.strip().upper().startswith(kw) for kw in safe_keywords):
        return {"result": "错误：只允许执行 MATCH/RETURN 类型的查询语句。"}

    try:
        # 执行查询
        with neo4j_driver.session(database=NEO4J_CONFIG['database']) as session:
            result = session.run(cypher, parameters=params or {})
            records = [record.data() for record in result]

            # 如果结果为空
            if not records:
                return {"result": "未查询到相关数据"}

            return {"result": records}

    except Exception as e:
        return {"result": f"图数据库查询失败: {str(e)}"}


# ============================================================
# ★ 新增：健康管理工具（Phase 1 - 核心 4 工具）
# ============================================================
# 设计原则：
#   1. 所有工具入参使用 email（保持前端兼容），内部通过 resolve_user_id 解析为 user_id
#   2. 工具内部调用 DAO 层，不直接操作数据库连接
#   3. 异常统一捕获并返回 {"status": "error", "result": "错误信息"}，保证 Agent 不会因工具崩溃而中断
# ============================================================

@mcp.tool(
    name="get_user_profile",
    description="获取用户的完整健康画像。Agent 在每次医疗咨询开始时应先调用此工具，"
                "了解用户的过敏史、慢性病和当前用药，以便给出个性化、安全的建议。"
)
async def get_user_profile(email: str) -> dict:
    """
    聚合查询用户的所有健康数据，包括：
    - 基本信息（年龄、性别、身高、体重、血型、生活习惯）
    - 过敏史列表
    - 慢性病列表
    - 当前用药列表

    为什么聚合在一个工具中而不是拆成 4 个？
    —— Agent 每次对话需要的是用户的完整画像，一次返回减少 Agent 的工具调用次数，
       降低延迟，也减少对数据库的查询压力。
    """
    try:
        user_id = resolve_user_id(email)

        # 并行聚合四张表的数据
        profile = HealthProfileDao.get_profile_by_user_id(user_id)
        allergies = UserAllergyDao.get_allergies_by_user_id(user_id)
        diseases = UserChronicDiseaseDao.get_diseases_by_user_id(user_id)
        medications = UserMedicationDao.get_medications_by_user_id(user_id, active_only=True)

        return {
            "status": "success",
            "result": {
                "profile": profile[0] if profile else {},
                "allergies": allergies,
                "chronic_diseases": diseases,
                "medications": medications
            }
        }
    except ValueError as e:
        # resolve_user_id 找不到用户时抛出 ValueError
        return {"status": "error", "result": str(e)}
    except Exception as e:
        return {"status": "error", "result": f"获取用户画像失败: {str(e)}"}


@mcp.tool(
    name="get_current_date",
    description="获取当前日期和星期。Agent 在回答任何时间敏感问题（如'什么时候开始吃药'、'吃了多久'、'昨天'、'最近'）"
                "时必须先调用此工具获取基准时间，禁止使用训练数据中的旧时间。"
)
async def get_current_date() -> dict:
    """
    返回今天的绝对日期和中文星期。

    为什么需要这个工具？
    —— Agent 是离线训练的大模型，不知道"今天"是哪天。
       用户问"我什么时候开始吃药"，Agent 必须知道今天才能推算"昨天"是几号。
    """
    today = get_today()
    return {
        "status": "success",
        "result": {
            "today": today.isoformat(),      # 如 "2026-08-15"
            "weekday": get_weekday_cn(today)  # 如 "周六"
        }
    }


@mcp.tool(
    name="update_user_profile",
    description="增量更新用户健康画像。Agent 在对话中识别到用户提供的健康信息时调用此工具。"
                "支持的 field 类型："
                "  - 基本信息字段: age, gender, height_cm, weight_kg, blood_type, smoking_status, alcohol_consumption, exercise_frequency"
                "  - 特殊字段: allergy（添加过敏史）, chronic_disease（添加慢性病）, medication（添加用药）, stop_medication（停用药物）"
                "date 参数：可选，用于记录时间信息。可以是绝对日期（如 2026-08-14）或相对时间（如 昨天、3个月前、半年前），"
                "工具内部会用 Python 的 datetime 库自动转换为绝对日期后写入数据库。"
)
async def update_user_profile(email: str, field: str, value: str, date: str = None) -> dict:
    """
    根据 field 类型自动路由到对应的 DAO 进行增量更新。

    设计考量：
    —— 为什么用"字段名 + 值"的字符串模式，而非结构化 JSON？
       1. Agent 生成结构化 JSON 的可靠性不如简单 key-value
       2. 与 Agent system prompt 中的指令风格一致（"调用 update_user_profile，参数 field=..., value=..."）
       3. 减少 Agent 幻觉：简单参数格式降低出错概率

    路由规则：
    —— 基本信息字段 → HealthProfileDao.update_profile（带类型转换）
    —— allergy → UserAllergyDao.add_allergy
    —— chronic_disease → UserChronicDiseaseDao.add_disease
    —— medication → UserMedicationDao.add_medication
    —— stop_medication → UserMedicationDao.stop_medication
    """
    try:
        user_id = resolve_user_id(email)

        # 路由表：基本信息字段（画像表标量字段）
        profile_fields = {
            'age', 'gender', 'height_cm', 'weight_kg', 'blood_type',
            'smoking_status', 'alcohol_consumption', 'exercise_frequency'
        }

        if field in profile_fields:
            # 类型转换：确保数值字段以正确的 Python 类型传给 MySQL
            # 为什么在这里转换而非在 DAO 层？—— 工具层负责参数校验和类型归一化，
            # DAO 层只负责数据操作，各司其职。
            converted_value = value
            if field == 'age':
                converted_value = int(value)
            elif field in ('height_cm', 'weight_kg'):
                converted_value = float(value)

            affected = HealthProfileDao.update_profile(user_id, **{field: converted_value})
            if affected == 0:
                # 画像不存在时自动创建（首次填写画像的场景）
                HealthProfileDao.create_profile(user_id, **{field: converted_value})
            return {"status": "success", "result": f"已更新 {field} = {value}"}

        elif field == 'allergy':
            UserAllergyDao.add_allergy(user_id, value)
            return {"status": "success", "result": f"已添加过敏史: {value}"}

        elif field == 'chronic_disease':
            # ★ 时间标准化：将相对/绝对时间描述转为 YYYY-MM-DD
            # 为什么在工具层用 Python 计算？—— LLM 做日期算术容易出错，
            #   由 datetime 库计算保证入库数据绝对准确。
            diagnosed_date = parse_relative_date(date) if date else None
            UserChronicDiseaseDao.add_disease(user_id, value, diagnosed_date=diagnosed_date)
            if diagnosed_date:
                date_info = f"，确诊日期 {diagnosed_date}"
            elif date:
                # ★ 优雅降级：解析失败时保留记录，但提示 Agent 追问用户
                date_info = f"（注意：日期'{date}'无法精确解析，已记录疾病但未记录具体日期，请向用户追问）"
            else:
                date_info = ""
            return {"status": "success", "result": f"已添加慢性病: {value}{date_info}"}

        elif field == 'medication':
            # ★ 时间标准化：相对时间（"昨天"、"3个月前"）→ 绝对日期 YYYY-MM-DD
            started_date = parse_relative_date(date) if date else None
            UserMedicationDao.add_medication(user_id, value, started_date=started_date)
            if started_date:
                date_info = f"，开始日期 {started_date}"
            elif date:
                # ★ 优雅降级：解析失败时保留药物记录，但提示 Agent 追问用户
                date_info = f"（注意：日期'{date}'无法精确解析，已记录药物但未记录具体日期，请向用户追问）"
            else:
                date_info = ""
            return {"status": "success", "result": f"已添加用药: {value}{date_info}"}

        elif field == 'stop_medication':
            # ★ 停药时记录 end_date = 今天，用于精确计算"服用时长"
            today = get_today().isoformat()
            UserMedicationDao.stop_medication(user_id, value, end_date=today)
            return {"status": "success", "result": f"已停用药物: {value}（停药日期 {today}）"}

        else:
            supported = sorted(profile_fields | {'allergy', 'chronic_disease', 'medication', 'stop_medication'})
            return {"status": "error", "result": f"不支持的字段: '{field}'。支持的字段: {supported}"}

    except ValueError as e:
        return {"status": "error", "result": str(e)}
    except Exception as e:
        return {"status": "error", "result": f"更新失败: {str(e)}"}


@mcp.tool(
    name="get_health_plans",
    description="查询用户的健康计划（饮食计划、运动计划、用药计划、综合计划）。"
                "Agent 在用户询问'我的计划'、'之前的饮食方案'时调用此工具。"
)
async def get_health_plans(email: str, plan_type: str = None) -> dict:
    """
    查询健康计划。

    参数 plan_type 设计为可选：
    —— 不传时返回所有类型的计划，Agent 可据此全面了解用户情况
    —— 传入时只返回特定类型（如 diet），减少返回数据量，提高响应速度
    """
    try:
        user_id = resolve_user_id(email)
        plans = HealthPlanDao.get_plans_by_user_id(
            user_id,
            plan_type=plan_type if plan_type else None,
            active_only=True
        )
        if not plans:
            return {"status": "success", "result": "暂无健康计划"}
        return {"status": "success", "result": plans}
    except ValueError as e:
        return {"status": "error", "result": str(e)}
    except Exception as e:
        return {"status": "error", "result": f"查询健康计划失败: {str(e)}"}


@mcp.tool(
    name="save_health_plan",
    description="保存 Agent 生成的健康计划。Agent 在为用户生成饮食方案、运动建议、"
                "用药提醒等计划后调用此工具，将计划持久化存储。"
)
async def save_health_plan(
    email: str,
    plan_type: str,
    title: str,
    content: str,
    start_date: str = None,
    end_date: str = None
) -> dict:
    """
    保存健康计划到 MySQL。

    为什么 content 设计为 str 而非 dict？
    —— Agent 生成的计划内容结构灵活多变（饮食计划包含食谱列表，运动计划包含动作组数），
       使用 JSON 字符串存储比固定的 dict schema 更灵活。应用层读取时自行解析。
    """
    try:
        user_id = resolve_user_id(email)

        # 参数校验：plan_type 必须为合法枚举值
        valid_types = {'diet', 'exercise', 'medication', 'comprehensive'}
        if plan_type not in valid_types:
            return {"status": "error", "result": f"无效的计划类型: '{plan_type}'，可选: {valid_types}"}

        plan_id = HealthPlanDao.save_plan(
            user_id, plan_type, title, content, start_date, end_date
        )
        return {"status": "success", "result": f"健康计划已保存，plan_id={plan_id}"}
    except ValueError as e:
        return {"status": "error", "result": str(e)}
    except Exception as e:
        return {"status": "error", "result": f"保存健康计划失败: {str(e)}"}


# ============================================================
# ★ Phase 2 新增：药物安全性评估工具
# ============================================================
# 设计原则：
#   1. 工具内部直接查 MySQL DAO + Neo4j，不依赖 Agent 工具链
#   2. Cypher 使用参数化查询，防止注入
#   3. 查无此药时返回空结构（触发 System Prompt 中的兜底逻辑）
#   4. 不做医学判断（contraindications/cautions 由 LLM 基于返回数据判定）
# ============================================================

@observe(name="evaluate_drug_safety", as_type="tool")
@mcp.tool(
    name="evaluate_drug_safety",
    description="评估指定药物对当前用户的安全性。返回该药物关联的疾病、症状，"
                "以及用户当前的健康数据，供 Agent 进行药物安全性判断。"
                "Agent 在推荐任何药物或回答用药问题前，必须先调用此工具。"
)
async def evaluate_drug_safety(email: str, drug_name: str) -> dict:
    """
    药物安全性评估工具。

    内部流程：
    1. 解析 user_id
    2. 查 MySQL 获取用户画像（过敏史、慢性病、当前用药）
    3. 查 Neo4j 获取药物关联的疾病和症状
    4. 交叉比对，返回结构化数据

    注意：此工具只提供数据，不做医学判断。禁忌症和慎用情况由 Agent（LLM）结合医学知识判定。
    """
    try:
        # step 1: 解析用户身份
        user_id = resolve_user_id(email)

        # step 2: 查 MySQL 获取用户健康数据
        allergies = UserAllergyDao.get_allergies_by_user_id(user_id)
        diseases = UserChronicDiseaseDao.get_diseases_by_user_id(user_id)
        medications = UserMedicationDao.get_medications_by_user_id(user_id, active_only=True)

        user_allergy_names = [a["allergy_name"] for a in allergies]
        user_disease_names = [d["disease_name"] for d in diseases]
        user_med_names = [m["medication_name"] for m in medications]

        # step 3: 查 Neo4j 获取药物信息（参数化查询）
        cypher_diseases = """
            MATCH (d:Disease)-[:DISEASE_DRUG]->(dr:Drug {name: $drug_name})
            RETURN d.name AS disease_name
        """
        cypher_symptoms = """
            MATCH (d:Disease)-[:DISEASE_DRUG]->(dr:Drug {name: $drug_name})
            MATCH (d)-[:DISEASE_SYMPTOM]->(s:Symptom)
            RETURN DISTINCT s.name AS symptom_name
        """

        drug_diseases = []
        drug_symptoms = []

        with neo4j_driver.session(database=NEO4J_CONFIG['database']) as session:
            # 查询药物关联的疾病
            result = session.run(cypher_diseases, parameters={"drug_name": drug_name})
            drug_diseases = [record["disease_name"] for record in result]

            # 查询药物关联的症状
            result = session.run(cypher_symptoms, parameters={"drug_name": drug_name})
            drug_symptoms = [record["symptom_name"] for record in result]

        # step 4: 交叉比对，组装返回结构
        # 为什么不在工具层做医学判断？
        # —— 工具只负责数据获取和交叉比对，医学判断（如判定"禁忌症"）是 LLM 的职责。
        #    工具提供数据清单，LLM 结合医学知识做出最终判断。

        # 药物关联疾病与用户慢性病的交集（可能是指征也可能是禁忌，由 LLM 判断）
        # ★ 加固 3：从"精确字符串匹配"改为"模糊/包含匹配"
        # 为什么？—— 用户可能记录"原发性高血压"，而图谱节点是"高血压"，
        #    精确匹配会漏掉这种同义不同名的情况，导致风险漏报。
        overlapping_diseases = []
        for drug_disease in drug_diseases:
            for user_disease in user_disease_names:
                if is_disease_match(user_disease, drug_disease):
                    overlapping_diseases.append(user_disease)
                    break  # 每个图谱疾病只记录一次匹配

        return {
            "status": "success",
            "result": {
                "drug": drug_name,
                # 药物在知识图谱中的关联数据
                "drug_related_diseases": drug_diseases,
                "drug_related_symptoms": drug_symptoms,
                # 用户健康数据（匿名化，仅提供清单供 LLM 交叉比对）
                "user_allergies": user_allergy_names,
                "user_diseases": user_disease_names,
                "user_medications": user_med_names,
                # 交叉比对结果
                "disease_overlap": overlapping_diseases,
                # DDI 说明
                "ddi_support": False,
                "ddi_note": "当前知识图谱不支持药物间相互作用查询。请 Agent 基于通用医学知识评估"
                             f" {drug_name} 与用户当前用药 {user_med_names} 的相互作用风险。",
                # 图谱覆盖度说明
                "knowledge_graph_note": (
                    f"图谱中该药物关联 {len(drug_diseases)} 种疾病、{len(drug_symptoms)} 种症状。"
                    if drug_diseases or drug_symptoms
                    else f"知识图谱中未收录药物 '{drug_name}' 的相关信息。"
                         f"请 Agent 基于通用医学知识进行评估，并明确告知用户此局限性。"
                )
            }
        }

    except ValueError as e:
        return {"status": "error", "result": str(e)}
    except Exception as e:
        return {"status": "error", "result": f"药物安全性评估失败: {str(e)}"}


# ============================================================
# ★ Phase 4 新增：疾病健康指导工具（get_disease_advice）
# ============================================================

def _disease_match_score(user_name: str, cand_name: str) -> int:
    """
    疾病名语义匹配打分（is_disease_match 的"打分版"）。

    为什么需要打分？—— CONTAINS 模糊匹配可能返回多个候选（如"高血压"命中"高血压"
    "原发性高血压"等），需要选出语义最贴近的那一个。

    打分规则（从严格到宽松，与 is_disease_match 的三策略一致）：
        精确匹配=3 > 规范化匹配=2 > 包含匹配=1 > 无匹配=0
    """
    if user_name == cand_name:
        return 3
    if normalize_disease_name(user_name) == normalize_disease_name(cand_name):
        return 2
    if user_name in cand_name or cand_name in user_name:
        return 1
    return 0


@observe(name="get_disease_advice", as_type="tool")
@mcp.tool(
    name="get_disease_advice",
    description="查询指定疾病的饮食/治疗健康指导。返回该疾病的宜吃食物、忌吃食物、推荐菜肴和治疗方式。"
                "Agent 在为用户生成个性化健康方案、饮食建议时，对每个慢性病逐一调用此工具。"
)
async def get_disease_advice(disease_name: str) -> dict:
    """
    查询疾病的健康指导数据（宜吃 / 忌吃 / 推荐菜肴 / 治疗方式）。

    为什么用两步模糊匹配？
    —— 用户记录的疾病名（如"血压高"）可能与图谱节点名（如"高血压"）不一致，
       直接精确匹配会漏查。第一步 CONTAINS 缩小候选范围，第二步语义打分选出最佳节点。
    """
    try:
        disease_name = (disease_name or "").strip()
        if not disease_name:
            return {"status": "error", "result": "疾病名称为空，无法查询"}

        # 第一步：Cypher 层 CONTAINS 模糊匹配（用规范化名提升召回率），限制 Top-3 候选
        norm_name = normalize_disease_name(disease_name)
        with neo4j_driver.session(database=NEO4J_CONFIG['database']) as session:
            result = session.run(
                "MATCH (d:Disease) WHERE d.name CONTAINS $name RETURN d.name AS name LIMIT 3",
                parameters={"name": norm_name}
            )
            candidates = [record["name"] for record in result]

        # 第二步：对候选列表做语义打分，取最高分作为最终疾病节点
        best_match, best_score = None, 0
        for cand in candidates:
            score = _disease_match_score(disease_name, cand)
            if score > best_score:
                best_match, best_score = cand, score

        if best_match is None:
            return {"status": "error", "result": "未找到该疾病的健康指导数据"}

        # 查询该疾病的宜吃 / 忌吃 / 菜肴 / 治疗方式
        cypher_advice = """
            MATCH (d:Disease {name: $name})
            OPTIONAL MATCH (d)-[:DISEASE_DO_EAT]->(doeat:Food)
            OPTIONAL MATCH (d)-[:DISEASE_NOT_EAT]->(noteat:Food)
            OPTIONAL MATCH (d)-[:DISEASE_DISHES]->(dish:Dishes)
            OPTIONAL MATCH (d)-[:DISEASE_CUREWAY]->(cure:Cureway)
            RETURN d.name AS disease,
                   collect(DISTINCT doeat.name) AS do_eat,
                   collect(DISTINCT noteat.name) AS not_eat,
                   collect(DISTINCT dish.name) AS dishes,
                   collect(DISTINCT cure.name) AS cureways
        """
        with neo4j_driver.session(database=NEO4J_CONFIG['database']) as session:
            record = session.run(cypher_advice, parameters={"name": best_match}).single()

        if not record:
            return {"status": "error", "result": "未找到该疾病的健康指导数据"}

        return {
            "status": "success",
            "result": {
                "disease": record["disease"],
                "do_eat": [x for x in record["do_eat"] if x],
                "not_eat": [x for x in record["not_eat"] if x],
                "dishes": [x for x in record["dishes"] if x],
                "cureways": [x for x in record["cureways"] if x],
            }
        }
    except Exception as e:
        return {"status": "error", "result": f"获取疾病健康指导失败: {str(e)}"}


# --- 新增代码结束 ---

if __name__ == '__main__':
    mcp.run(
        transport="http",
        host=env("MCP_HOST", "0.0.0.0"),
        port=9000,
        path="/mcp",
        show_banner=False
    )