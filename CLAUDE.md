# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A medical knowledge RAG (Retrieval-Augmented Generation) system with two services:

- **rag_server** — Python FastAPI backend (port 8000). AI agent powered by LangChain + Qwen LLM (Alibaba DashScope), with tools for Neo4j medical knowledge graph queries, email verification, weather, route planning, and POI search. Uses MCP (Model Context Protocol) for tool execution.
- **rag_app** — Vue.js 2 + Webpack 3 frontend (port 8080). Chat UI with login, registration, and conversation history. Uses Element UI component library.

## Commands

### Frontend (rag_app/)

```bash
cd rag_app
npm install                # Install dependencies
npm run dev                # Dev server at localhost:8080 with hot reload
npm run build              # Production build to dist/
```

### Backend (rag_server/)

```bash
cd rag_server
python main.py             # Start FastAPI server at localhost:8000
```

### MCP Server (required for backend agent tools)

```bash
cd rag_server
python mymcp/MCPServer.py  # Start MCP server at localhost:9000/mcp
```

## Architecture

### Backend (rag_server/) — Layered Architecture

```
main.py                         # FastAPI app entry, lifespan, CORS (allow localhost:8080), router registration
├── ai/                         # AI agent and tool definitions
│   ├── LoadAgent.py            # create_agent with system_prompt defining 5 workflow flows
│   ├── LoadLLM.py              # ChatOpenAI → Qwen via DashScope (kimi-k3)
│   ├── LoadTools.py            # Tool functions: find_email, send_email, verify_code, find_data, query_weather, plan_route, search_poi
│   └── AmapUtil.py             # Amap (高德) API helper, reads AMAP_API_KEY from env
├── chat/
│   ├── controller/             # FastAPI routers: ChatController (SSE streaming), HistoryController (CRUD)
│   ├── service/                # Business logic: chat invocation, history CRUD, message batching
│   ├── dao/                    # MySQL queries for history table
│   └── utils/
│       ├── ChatUtil.py         # GraphCypherQAChain — non-agent RAG path using Neo4j graph directly
│       └── MySQLUtil.py        # MySQL connection for chat module
├── users/
│   ├── controller/             # Auth endpoints: sendEmail, verifyCode, register, deleteAccount
│   ├── service/                # Agent-driven email verification + user registration
│   └── dao/                    # User CRUD via common/MySQLUtil
├── common/
│   ├── MySQLUtil.py            # Shared MySQL helpers (execute_query, execute_insert, execute_update)
│   ├── ResponseUtil.py         # Unified response formatters + agent message extraction
│   └── UserUtil.py             # email → user_id resolver (门面模式，保持前端兼容)
├── health/                     # ★ 用户健康管理模块 (Phase 1)
│   └── dao/
│       ├── HealthProfileDao.py # user_profiles 表 CRUD（含 upsert）
│       ├── UserAllergyDao.py   # user_allergies 表 CRUD（INSERT IGNORE 去重）
│       ├── UserChronicDiseaseDao.py  # user_chronic_diseases 表 CRUD
│       ├── UserMedicationDao.py      # user_medications 表 CRUD（软删除停药）
│       └── HealthPlanDao.py    # health_plans 表 CRUD（软删除归档）
├── entity/                     # Pydantic models: UserInfo, HistoryInfo
├── sql/
│   └── init_health_tables.sql  # 健康模块 5 张表建表脚本
└── mymcp/
    ├── MCPServer.py            # FastMCP server: 8 tools (4 原有 + 4 健康管理)
    └── MCPClient.py            # Async HTTP client calling MCP server at localhost:9000
```

**Two RAG paths exist:**

1. **Agent path** ( /chat/chatAgentStream) — LangChain create_agent with tool-calling. The LLM decides which tool to invoke. Tool execution happens via MCP server. Returns SSE stream with text and tool event types.
2. **Non-agent path** ( /chat/chatNoAgentStream) — Uses GraphCypherQAChain directly. LLM generates Cypher → executes against Neo4j → LLM summarizes results. Simpler but limited to medical knowledge queries only.

**Infrastructure dependencies (all expected on localhost):**
- MySQL (suse_agent database) — 7 tables:
  - users (user_id, username, email)
  - history (history_id, question, answer, parent_id, email, title, create_time)
  - user_profiles — 健康画像：年龄、性别、身高体重、血型、生活习惯
  - user_allergies — 过敏史：过敏原名称、严重程度
  - user_chronic_diseases — 慢性病：疾病名称、确诊日期
  - user_medications — 当前用药：药物名称、剂量、频率
  - health_plans — 健康计划：饮食/运动/用药/综合计划
- Neo4j — medical knowledge graph with nodes (Disease, Symptom, Check, Drug, Department, Food, Dishes, Category, Cureway) and their relationships
- Redis — email verification code storage (60s TTL)
- MCP Server (port 9000) — tool execution layer for MySQL queries, email sending, verification code validation, Neo4j Cypher execution, and user health profile management

### Frontend (rag_app/) — Vue 2 SPA

```
src/
├── main.js               # Vue init, Element UI, axios (baseURL: localhost:8000), markdown-it
├── App.vue               # Root component, <router-view/>
├── router/index.js        # Hash-mode routes: / → Login, /chat → Chat, /register → Register
└── views/
    ├── Login.vue          # Email verification code login flow
    ├── Register.vue       # User registration
    └── Chat.vue           # Main chat interface with sidebar history, SSE streaming, search, rename/delete
```

**Key patterns:**
- Vue.prototype.$axios — global axios instance for API calls
- Vue.prototype.$md + Vue.filter('markdown') — render markdown in chat responses
- Chat uses SSE (Server-Sent Events) via EventSource for streaming responses from both agent and non-agent endpoints
- History sidebar: create, switch, rename, delete conversations; keyword search
- Login state managed via sessionStorage for email

## Environment Variables

The backend requires these environment variables:
- DASHSCOPE_API_KEY — Alibaba DashScope API key for Qwen LLM
- AMAP_API_KEY — Amap (高德地图) API key for weather, route planning, POI search

## Startup Order

1. Start MySQL, Neo4j, and Redis services
2. **首次部署**：执行建表脚本 mysql -u root -p suse_agent < rag_server/sql/init_health_tables.sql
3. Start MCP server: python rag_server/mymcp/MCPServer.py
4. Start backend: python rag_server/main.py
5. Start frontend: cd rag_app && npm run dev

## 全栈协作规范（强制）

**后端优先原则**：当涉及新增或修改数据表（如用户画像、健康计划）时，必须先在 rag_server 中完成数据库设计和 API 开发。

**API 契约记录**：后端 API 确定后，必须在 CLAUDE.md 的【API 契约】章节中显式记录接口路径、请求方法、请求参数和返回 JSON 格式。

**前端开发依据**：开发前端对应页面时，必须严格参照【API 契约】章节的约定，禁止自行编造接口或字段名。

**联调交付标准**：任何涉及前后端联调的任务，输出结果必须同时包含：后端修改方案（SQL/Python）+ 前端调用代码（Vue/React），并说明如何联调。

## API 契约

### MCP 工具契约（Phase 1 — 健康管理模块）

以下 MCP 工具已在 mymcp/MCPServer.py 中实现，Agent 通过 MCPClient.py 调用。

| 工具名称 | 入参 | 返回值 | 职责 |
|---------|------|--------|------|
| get_user_profile | email: str | {"result": {"profile": {...}, "allergies": [...], "chronic_diseases": [...], "medications": [...]}} | 获取用户完整健康画像（聚合 4 张表，含 started_date/end_date） |
| update_user_profile | email: str, field: str, value: str, date: str = None | {"result": "已更新 field = value"} | 增量更新画像字段，自动路由到对应 DAO；date 支持绝对日期或相对时间，工具层自动标准化 |
| get_current_date | 无 | {"result": {"today": "YYYY-MM-DD", "weekday": "周X"}} | 获取当前日期和星期，供 Agent 回答时间敏感问题 |
| get_health_plans | email: str, plan_type: str = None | {"result": [...]} | 查询用户健康计划，可按类型筛选 |
| save_health_plan | email: str, plan_type: str, title: str, content: str, start_date: str = None, end_date: str = None | {"result": "健康计划已保存，plan_id=N"} | 保存 Agent 生成的健康计划 |

**update_user_profile 支持的 field 路由：**
- 基本信息: age, gender, height_cm, weight_kg, blood_type, smoking_status, alcohol_consumption, exercise_frequency
- 特殊字段: allergy（添加过敏史）, chronic_disease（添加慢性病，date→确诊日期）, medication（添加用药，date→开始日期）, stop_medication（停用药物，自动记录 end_date）

**时间标准化**：`common/DateUtil.py` 的 `parse_relative_date` 将"昨天/3个月前/半年前"等相对时间转为绝对日期 `YYYY-MM-DD`，由 Python datetime 库计算，不依赖 LLM 算术。

### MCP 工具契约（Phase 2 — 药物安全性评估）

| 工具名称 | 入参 | 返回值 | 职责 |
|---------|------|--------|------|
| evaluate_drug_safety | email: str, drug_name: str | {"result": {"drug": str, "drug_related_diseases": [...], "drug_related_symptoms": [...], "user_allergies": [...], "user_diseases": [...], "user_medications": [...], "disease_overlap": [...], "ddi_support": bool, "ddi_note": str, "knowledge_graph_note": str}} | 评估药物安全性：查 Neo4j 药物关联数据 + 用户健康数据交叉比对，供 Agent 判断禁忌症/慎用/症状风险 |

**DDI 说明**：当前 Neo4j Schema 无 `Drug-[:INTERACTS_WITH]->Drug` 关系，`ddi_support` 恒为 `False`，DDI 判断依赖 LLM 医学知识。

### FastAPI REST 契约

（待后续 Phase 3 开发完成后逐条补充）
