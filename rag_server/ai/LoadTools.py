# 导入MCP客户端封装的函数
from mymcp import MCPClient
from typing import Dict, Any
# ★ 新增：导入高德地图 API 工具函数（与 LoadLLM.py 风格一致）
from ai.AmapUtil import get as amap_get

"""
在这里的工具定义函数中，需要通过函数描述文档来给agent说明这个工具中的信息、调用规则等【必须写】
"""

# 查询MySQL数据库数据的工具
def find_email(sql: str, params: str | None = None) -> Dict[str, Any]:
    """
    数据库中有一张用户表 users，其结构信息如下：
        user_id: 主键自增ID
        username: 用户名
        email: 邮箱号
    在通过用户名查询邮箱号信息的时候调用这个工具，这个工具只能够实现查询操作，比如：
    'select * from users where username=%s'
    """
    return MCPClient.call_mcp_tool(tool_name="find_email", sql=sql, params=params or "")

# 发送邮件的工具
def send_email(receiver: str) -> Dict[str, Any]:
    """
    在发送邮件的时候调用这个工具
    """
    return MCPClient.call_mcp_tool(tool_name="send_email", receiver=receiver)

# 验证验证码的工具
def verify_code(receiver: str, code: str) -> Dict[str, Any]:
    """
    在执行验证码验证的时候调用这个工具
    receiver: 收件方的邮箱号，作为redis查询的key
    code: 用户输入的验证码
    """
    return MCPClient.call_mcp_tool(tool_name="verify_code", receiver=receiver, code=code)


def find_data(cypher: str, params: dict | None = None) -> Dict[str, Any]:
    """
    如果涉及到疾病信息查询，先查询neo4j数据库中的数据
    只查询用户问题相关的内容信息
    关于疾病查询的数据存储的关系信息如下：
        | 关系类型                 | 含义说明          | 指向节点         |
        | -------------------- | ------------- | ------------ |
        | `DISEASE_ACOMPANY`   | 疾病的并发症 / 伴随疾病 | `Disease`    |
        | `DISEASE_CATEGORY`   | 疾病所属类别        | `Category`   |
        | `DISEASE_CHECK`      | 疾病相关检查项目      | `Check`      |
        | `DISEASE_CUREWAY`    | 疾病治疗方式        | `Cureway`    |
        | `DISEASE_DEPARTMENT` | 就诊科室          | `Department` |
        | `DISEASE_DISHES`     | 适合疾病的菜肴       | `Dishes`     |
        | `DISEASE_DO_EAT`     | 推荐进食的食物       | `Food`       |
        | `DISEASE_NOT_EAT`    | 不推荐进食的食物      | `Food`       |
        | `DISEASE_DRUG`       | 治疗或相关药物       | `Drug`       |
        | `DISEASE_SYMPTOM`    | 疾病症状          | `Symptom`    |
    关于疾病查询的节点信息如下：
        | 节点标签         | 含义       |
        | ------------ | -------- |
        | `Disease`    | 疾病（核心节点） |
        | `Category`   | 疾病分类     |
        | `Check`      | 检查项目     |
        | `Cureway`    | 治疗方式     |
        | `Department` | 科室       |
        | `Dishes`     | 菜肴       |
        | `Food`       | 食物       |
        | `Drug`       | 药物       |
        | `Symptom`    | 症状       |
    """
    return MCPClient.call_mcp_tool(
        tool_name="find_data",
        cypher=cypher,
        params=params or {}
    )


# ★ 修改：天气查询工具（与 LoadLLM 风格一致，无 try/except）
def query_weather(city: str) -> dict:
    """
    查询指定城市的天气信息
    当用户询问某个城市的天气时调用此工具
    city: 城市名，如'北京'、'上海'
    """
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {"city": city, "extensions": "all"}
    return {"result": amap_get(url, params)}


# ★ 修改：统一路线规划工具（支持驾车/步行/骑行/电动车/公交，API 升级为 v5）
def plan_route(origin: str, destination: str, type: str = "driving") -> dict:
    """
    路线规划工具。
    当用户询问驾车路线、导航、开车怎么走、步行、骑行、电动车、公交路线等问题时调用此工具。

    参数说明:
        origin: 起点位置，支持中文地名（如"北京"、"上海"、"天安门"）
        destination: 终点位置，支持中文地名
        type: 路线类型
            "driving" - 驾车
            "walking" - 步行
            "bicycling" - 骑行
            "electrobike" - 电动车
            "transit" - 公交
    返回:
        包含路线信息的字典
    """
    # 第一步：地理编码（地名转坐标）
    geo_url = "https://restapi.amap.com/v3/geocode/geo"
    origin_data = amap_get(geo_url, {"address": origin})
    dest_data = amap_get(geo_url, {"address": destination})
    origin_loc = origin_data.get("geocodes", [{}])[0].get("location")
    dest_loc = dest_data.get("geocodes", [{}])[0].get("location")

    # 第二步：根据 type 选择 v5 endpoint
    endpoints = {
        "driving": "driving",
        "walking": "walking",
        "bicycling": "bicycling",
        "electrobike": "electrobike",
        "transit": "transit/integrated",
    }
    endpoint = endpoints.get(type, "driving")
    url = f"https://restapi.amap.com/v5/direction/{endpoint}"
    params = {"origin": origin_loc, "destination": dest_loc}

    # 公交需要传城市代码（从地理编码结果中提取 adcode）
    if type == "transit":
        params["city1"] = origin_data.get("geocodes", [{}])[0].get("adcode")
        params["city2"] = dest_data.get("geocodes", [{}])[0].get("adcode")

    return {"result": amap_get(url, params)}


# ★ 新增：周边搜索（POI）工具
def search_poi(location: str, keywords: str = None, radius: int = 1000) -> dict:
    """
    周边搜索工具。
    当用户查询某个位置附近的医院、药店、餐馆、银行等POI（兴趣点）时调用此工具。

    参数说明:
        location: 中心点坐标（如"116.397428,39.90923"）
        keywords: 关键词（如"医院"、"药店"）
        radius: 搜索半径（米，可选，默认1000）
    返回:
        包含POI列表的字典（名称、地址、距离等）
    """
    url = "https://restapi.amap.com/v3/place/around"
    params = {"location": location, "radius": radius}
    if keywords:
        params["keywords"] = keywords
    return {"result": amap_get(url, params)}


# ============================================================
# ★ Phase 1 新增：健康管理工具（4 个核心工具）
# ============================================================

def get_user_profile(email: str) -> Dict[str, Any]:
    """
    获取用户的完整健康画像。
    当用户询问自己的健康数据、过敏史、慢性病、当前用药时，必须先调用此工具。
    返回的数据包括：
        - profile: 基本信息（年龄、性别、身高体重、血型、生活习惯）
        - allergies: 过敏史列表
        - chronic_diseases: 慢性病列表
        - medications: 当前用药列表
    """
    return MCPClient.call_mcp_tool(tool_name="get_user_profile", email=email)


def update_user_profile(email: str, field: str, value: str, date: str = None) -> Dict[str, Any]:
    """
    增量更新用户健康画像的某个字段。
    支持的 field 类型：
        - 基本信息: age, gender, height_cm, weight_kg, blood_type, smoking_status, alcohol_consumption, exercise_frequency
        - 特殊字段: allergy（添加过敏史）, chronic_disease（添加慢性病）, medication（添加用药）, stop_medication（停用药物）
    date 参数：可选。用于记录时间信息，支持绝对日期（"2026-08-14"）或相对时间（"昨天"、"3个月前"、"半年前"）。
    当用户在对话中提及自己的健康信息时（如"我昨天开始吃二甲双胍"），应调用此工具记录，并传入时间。
    """
    return MCPClient.call_mcp_tool(tool_name="update_user_profile", email=email, field=field, value=value, date=date or "")


def get_current_date() -> Dict[str, Any]:
    """
    获取当前日期和星期。
    当用户询问任何时间敏感问题（如"什么时候开始吃药"、"吃了多久"、"昨天"、"最近"）时，
    必须先调用此工具获取基准时间，禁止使用训练数据中的旧时间。
    """
    return MCPClient.call_mcp_tool(tool_name="get_current_date")


def get_health_plans(email: str, plan_type: str = None) -> Dict[str, Any]:
    """
    查询用户的健康计划（饮食/运动/用药/综合）。
    当用户询问"我的计划"、"之前的饮食方案"、"有什么运动建议"时调用此工具。
    """
    return MCPClient.call_mcp_tool(tool_name="get_health_plans", email=email, plan_type=plan_type or "")


def save_health_plan(email: str, plan_type: str, title: str, content: str,
                     start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    保存健康计划到数据库。
    当 Agent 为用户生成了饮食方案、运动建议、用药提醒等计划后，调用此工具持久化存储。
    plan_type 可选值: diet（饮食）, exercise（运动）, medication（用药）, comprehensive（综合）
    """
    return MCPClient.call_mcp_tool(
        tool_name="save_health_plan",
        email=email, plan_type=plan_type, title=title, content=content,
        start_date=start_date or "", end_date=end_date or ""
    )


# ============================================================
# ★ Phase 2 新增：药物安全性评估工具
# ============================================================

def evaluate_drug_safety(email: str, drug_name: str) -> Dict[str, Any]:
    """
    评估指定药物对当前用户的安全性。

    当用户询问"我能不能吃XX药"、"XX药安全吗"、推荐药物等用药问题时，必须先调用此工具。
    返回该药物在知识图谱中关联的疾病和症状，以及用户当前的健康数据，供 Agent 进行药物安全性判断。

    参数说明:
        email: 用户邮箱（用于查健康画像）
        drug_name: 单一药物的通用名（如"布洛芬"、"对乙酰氨基酚"）
    """
    return MCPClient.call_mcp_tool(tool_name="evaluate_drug_safety", email=email, drug_name=drug_name)


# ============================================================
# ★ Phase 4 新增：疾病健康指导工具
# ============================================================

def get_disease_advice(disease_name: str) -> Dict[str, Any]:
    """
    查询指定疾病的健康指导（宜吃食物、忌吃食物、推荐菜肴、治疗方式）。
    当用户要求生成个性化健康方案、饮食建议时，对每个慢性病调用此工具获取图谱数据。
    """
    return MCPClient.call_mcp_tool(tool_name="get_disease_advice", disease_name=disease_name)