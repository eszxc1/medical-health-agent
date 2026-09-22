# Neo4j 图谱数据初始化说明

本项目用 Neo4j 存储**医学知识图谱**（疾病、症状、检查、药物、食物等节点及其关联）。要跑通「药物安全性评估」「知识图谱问答」「个性化健康方案」等核心功能。完整数据会在 `docker compose up` 时由内置的 `neo4j-import` 服务**自动批量导入**（约 2.7 万节点 / 38 万关系）；本文档提供 Schema 说明，以及「最小可演示图谱」的**手动导入**方式（离线调试/快速体验用）。

> 说明：`rag_server/sql/` 下的脚本是 **MySQL** 建表脚本，与 Neo4j 无关；完整图谱数据由 `neo4j-import` 服务自动导入。下面的 Cypher 仅用于**手动**导入「最小可演示图谱」（离线调试/快速体验用）。

## 一、节点与关系 Schema

### 9 类节点

| 节点标签 | 含义 |
|---------|------|
| `Disease` | 疾病（核心节点） |
| `Symptom` | 症状 |
| `Check` | 检查项目 |
| `Drug` | 药物 |
| `Department` | 就诊科室 |
| `Food` | 食物 |
| `Dishes` | 菜肴 |
| `Category` | 疾病分类 |
| `Cureway` | 治疗方式 |

### 关系类型

| 关系类型 | 含义 | 起点 → 终点 |
|---------|------|-------------|
| `DISEASE_SYMPTOM` | 疾病症状 | Disease → Symptom |
| `DISEASE_CHECK` | 相关检查 | Disease → Check |
| `DISEASE_CUREWAY` | 治疗方式 | Disease → Cureway |
| `DISEASE_DRUG` | 相关药物 | Disease → Drug |
| `DISEASE_DEPARTMENT` | 就诊科室 | Disease → Department |
| `DISEASE_DO_EAT` | 宜吃食物 | Disease → Food |
| `DISEASE_NOT_EAT` | 忌口食物 | Disease → Food |
| `DISEASE_DISHES` | 推荐菜肴 | Disease → Dishes |
| `DISEASE_ACOMPANY` | 并发症 | Disease → Disease |
| `DISEASE_CATEGORY` | 疾病分类 | Disease → Category |

## 二、导入最小可演示图谱

下面的 Cypher 以「高血压」为主疾病，覆盖全部 9 类节点与多数关系，并用「2 型糖尿病」演示并发症（`DISEASE_ACOMPANY`）多跳关系。

```cypher
// ===== 核心疾病：高血压 =====
CREATE (htn:Disease {name: "高血压"})
CREATE (s_head:Symptom {name: "头痛"})
CREATE (s_dizzy:Symptom {name: "头晕"})
CREATE (check:Check {name: "血压测量"})
CREATE (drug_nife:Drug {name: "硝苯地平"})
CREATE (drug_amlo:Drug {name: "氨氯地平"})
CREATE (dep:Department {name: "心内科"})
CREATE (food_eat:Food {name: "芹菜"})
CREATE (food_not:Food {name: "咸菜"})
CREATE (dish:Dishes {name: "清蒸鲈鱼"})
CREATE (cat:Category {name: "心血管疾病"})
CREATE (cureway:Cureway {name: "药物治疗"})

// 高血压 关联关系
CREATE (htn)-[:DISEASE_SYMPTOM]->(s_head)
CREATE (htn)-[:DISEASE_SYMPTOM]->(s_dizzy)
CREATE (htn)-[:DISEASE_CHECK]->(check)
CREATE (htn)-[:DISEASE_DRUG]->(drug_nife)
CREATE (htn)-[:DISEASE_DRUG]->(drug_amlo)
CREATE (htn)-[:DISEASE_DEPARTMENT]->(dep)
CREATE (htn)-[:DISEASE_DO_EAT]->(food_eat)
CREATE (htn)-[:DISEASE_NOT_EAT]->(food_not)
CREATE (htn)-[:DISEASE_DISHES]->(dish)
CREATE (htn)-[:DISEASE_CATEGORY]->(cat)
CREATE (htn)-[:DISEASE_CUREWAY]->(cureway)

// ===== 并发症：2 型糖尿病（演示多跳 DISEASE_ACOMPANY）=====
CREATE (t2dm:Disease {name: "2型糖尿病"})
CREATE (drug_met:Drug {name: "二甲双胍"})
CREATE (htn)-[:DISEASE_ACOMPANY]->(t2dm)
CREATE (t2dm)-[:DISEASE_DRUG]->(drug_met)
```

### 如何执行

**方式一：Neo4j Browser（推荐）**

1. 启动 Neo4j 后打开浏览器界面：`http://localhost:7475`（Bolt 为 `bolt://localhost:7688`）
2. 用账号 `neo4j`、密码（见 `.env` 的 `NEO4J_PASSWORD`）登录
3. 把上面的 Cypher 粘贴到输入框执行

**方式二：cypher-shell（Docker）**

```bash
docker exec -it rag-neo4j cypher-shell -u neo4j -p <你的密码>
```

### 验证导入结果

```cypher
// 查主疾病节点
MATCH (d:Disease {name: "高血压"}) RETURN d

// 查一键全部关联
MATCH (d:Disease {name:"高血压"})-[r]->(x)
RETURN d.name, type(r), labels(x), x.name

// 多跳示例：高血压 -> 并发症 -> 药物（应有 二型糖尿病 -> 二甲双胍）
MATCH (d:Disease {name:"高血压"})-[:DISEASE_ACOMPANY]->(c:Disease)-[:DISEASE_DRUG]->(dr:Drug)
RETURN d.name, c.name, dr.name
```

## 三、MySQL 健康档案测试数据

图谱初始化后，还需要给某个用户插入**健康档案测试数据**（画像 / 过敏史 / 慢病 / 用药），用于演示「个性化用药评估」。

前置条件：

1. 已在系统注册该用户（邮箱需存在于 `users` 表）。
2. MySQL 已运行，且健康模块 5 张表已建（`rag_server/sql/init_health_tables.sql`）。

执行脚本：

```bash
cd rag_server
# 默认给 test@example.com 插入测试数据，也可传自定义邮箱
python scripts/insert_test_data.py test@example.com
```

该脚本会插入：

- **画像**：55 岁男性，172cm/78kg，A 型血，戒烟，偶尔饮酒，每周运动 2 次
- **过敏史**：青霉素（重度）、磺胺类药物（中度）、花粉（轻度）
- **慢性病**：高血压、2 型糖尿病、高脂血症
- **当前用药**：硝苯地平、二甲双胍、阿托伐他汀

插入成功后，可在前端询问：`记得我的过敏史吗？`、`我现在在吃什么药？`、`我能不能吃布洛芬` 来验证个性化回答与药物冲突检测。