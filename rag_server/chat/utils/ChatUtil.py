from ai import LoadLLM
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_core.prompts import PromptTemplate

from common.config import env, required_env

class ChatUtil:
    @staticmethod
    def chat(question: str):
        # 加载大模型
        llm = LoadLLM.load_model()
        # 加载neo4j连接
        graph = Neo4jGraph(
            url=env("NEO4J_URI", "neo4j://127.0.0.1:7687"),
            username=env("NEO4J_USERNAME", "neo4j"),
            password=required_env("NEO4J_PASSWORD"),
            database=env("NEO4J_DATABASE", "neo4j"),
        )

        neo4j_prompt_template =  """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}

# 节点标签及含义
| 节点标签     | 含义             |
|--------------|------------------|
| Disease      | 疾病（核心节点） |
| Symptom      | 症状             |
| Check        | 检查项目         |
| Cureway      | 治疗方式         |
| Drug         | 药物             |
| Department   | 就诊科室         |
| Food         | 食物             |
| Dishes       | 菜肴             |
| Category     | 疾病分类         |

# 关系类型及含义
| 关系类型             | 含义              | 起始节点 | 目标节点    |
|----------------------|-------------------|----------|-------------|
| DISEASE_SYMPTOM      | 疾病症状          | Disease  | Symptom     |
| DISEASE_CHECK        | 相关检查项目      | Disease  | Check       |
| DISEASE_CUREWAY      | 治疗方式          | Disease  | Cureway     |
| DISEASE_DRUG         | 治疗或相关药物    | Disease  | Drug        |
| DISEASE_DEPARTMENT   | 就诊科室          | Disease  | Department  |
| DISEASE_DO_EAT       | 推荐进食的食物    | Disease  | Food        |
| DISEASE_NOT_EAT      | 不推荐进食的食物  | Disease  | Food        |
| DISEASE_DISHES       | 适合疾病的菜肴    | Disease  | Dishes      |
| DISEASE_ACOMPANY     | 并发症 / 伴随疾病 | Disease  | Disease     |
| DISEASE_CATEGORY     | 疾病所属类别      | Disease  | Category    |

# 查询示例
# 问：高血压有哪些症状？
MATCH (d:Disease {{name:"高血压"}})-[:DISEASE_SYMPTOM]->(s:Symptom) RETURN s.name AS symptom

# 问：感冒吃什么药？
MATCH (d:Disease {{name:"感冒"}})-[:DISEASE_DRUG]->(dr:Drug) RETURN dr.name AS drug

# 问：糖尿病不宜吃什么？
MATCH (d:Disease {{name:"糖尿病"}})-[:DISEASE_NOT_EAT]->(f:Food) RETURN f.name AS food

# 问：肺炎需要做什么检查？
MATCH (d:Disease {{name:"肺炎"}})-[:DISEASE_CHECK]->(c:Check) RETURN c.name AS check_item

# 问：高血压挂什么科？
MATCH (d:Disease {{name:"高血压"}})-[:DISEASE_DEPARTMENT]->(dep:Department) RETURN dep.name AS department

# 问：感冒的并发症有哪些？
MATCH (d:Disease {{name:"感冒"}})-[:DISEASE_ACOMPANY]->(a:Disease) RETURN a.name AS complication

# 问：糖尿病属于哪类疾病？
MATCH (d:Disease {{name:"糖尿病"}})-[:DISEASE_CATEGORY]->(c:Category) RETURN c.name AS category

# 问：高血压可以吃什么菜？
MATCH (d:Disease {{name:"高血压"}})-[:DISEASE_DISHES]->(dishes:Dishes) RETURN dishes.name AS dishes

# 问：哪些疾病会有头痛症状？
MATCH (d:Disease)-[:DISEASE_SYMPTOM]->(s:Symptom {{name:"头痛"}}) RETURN d.name AS disease

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{question}"""

        # 构造提示词对象
        neo4j_prompt = PromptTemplate(
            template=neo4j_prompt_template,
            input_variables=["schema", "question"]
        )

        qa_prompt_template = """你是一名专业的医疗智能问答助手，基于 Neo4j 疾病知识图谱为用户提供准确的健康咨询。

# 第一步：意图识别
判断用户问题是否属于【医疗疾病类】，包括但不限于：
- 疾病症状、病因、并发症
- 检查项目、就诊科室
- 治疗方式、用药建议
- 饮食宜忌、推荐菜肴
- 疾病分类与归属

# 第二步：按类别处理

## 情形 1：属于医疗疾病类 → 基于以下图谱查询结果作答
- 严格基于查询结果作答，不得编造疾病、药物或诊疗方案
- 若查询结果为空，回复："知识库中未收录该疾病的相关信息，建议咨询专业医生"

## 情形 2：不属于医疗疾病类
- 忽略知识图谱查询结果
- 基于自身通用知识自然作答
- 回复中不得出现"知识库""图谱""上下文"等字样

# 输出要求
- 直接给出最终答案，不复述问题、不解释判断过程
- 涉及用药、治疗、剂量等敏感内容时，附加一句："具体方案请遵医嘱"
- 语言简洁、准确、通俗易懂

---
【图谱查询结果】
{context}

【用户问题】
{question}

【回答】
"""

        qa_prompt = PromptTemplate(
            template=qa_prompt_template,
            input_variables=["context", "question"]
        )

        chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            cypher_prompt=neo4j_prompt,
            qa_prompt=qa_prompt,
            verbose=True,
            allow_dangerous_requests=True
        )
        response = chain.invoke({"query": question})
        # 函数内部允许return，供Service、Controller接口拿到返回值
        return response['result']