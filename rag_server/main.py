import traceback
from contextlib import asynccontextmanager

from common.config import env

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ai import LoadAgent
from fastapi.middleware.cors import CORSMiddleware

from chat.controller.HistoryController import history_router
from users.controller.UsersController import users_router
from chat.controller.ChatController import chat_router


# 生命周期管理（必须在创建 app 之前定义）
@asynccontextmanager
async def on_start(app: FastAPI):
    # ★ 移除 checkpointer，直接构建 agent（无记忆）
    try:
        app.state.agent = LoadAgent.load_agent()
        print("FastAPI 服务器启动了，创建了 agent 对象")
    except Exception as e:
        print(f"⚠️ Agent 创建失败: {e}")
        traceback.print_exc()
        app.state.agent = None
        print("FastAPI 服务器已启动，但 Agent 不可用（请检查 DASHSCOPE_API_KEY 和网络连接）")
    yield
    app.state.agent = None
    print("FastAPI 服务器关闭了，销毁了 agent 对象")

# 创建FastAPI实例（只定义一次）
app = FastAPI(lifespan=on_start)


# ★ 健康检查端点（供 docker-compose healthcheck 探测）
@app.get("/health")
def health():
    # agent 是否就绪只作为信息返回，不因 agent 创建失败而让 healthcheck 失败
    return {
        "status": "ok",
        "agent_ready": getattr(app.state, "agent", None) is not None,
    }


# ★ 兜底中间件：确保所有响应（包括未捕获异常的 500）都带 CORS 头
# 为什么需要这个中间件？
# —— FastAPI 的 CORSMiddleware 对未捕获异常产生的 500 响应可能不添加 CORS 头，
#    导致浏览器报 CORS 错误而掩盖了真正的 500 问题。
#    这个中间件捕获所有异常，返回带 CORS 头的 JSON 错误响应。
@app.middleware("http")
async def catch_all_and_add_cors(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "msg": f"服务器内部错误: {str(e)}"
            }
        )


# 注册子路由（只注册一次）
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(history_router, prefix="/history", tags=["history"])

# 配置跨域请求（必须在路由注册之后，确保作为最外层包装）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[env("CORS_ORIGINS", "http://localhost:8080")],  # 允许的源
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"],  # 允许的请求方法
    allow_headers=["*"],  # 允许的请求头
)


if __name__ == '__main__':
    uvicorn.run(
        app="main:app",
        host=env("APP_HOST", "localhost"),
        port=int(env("APP_PORT", "8000")),
        reload=False,
    )