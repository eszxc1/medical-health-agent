"""
Langfuse 全链路追踪集成
======================
基于 langfuse 4.x（OpenTelemetry 后端）：
- get_langfuse_handler()：返回 LangChain 的 CallbackHandler（单例），供 ChatOpenAI / agent.invoke 使用
- observe：@observe 装饰器，追踪自定义函数（Neo4j 查询、MCP 工具等）

关键机制（langfuse 4.x）：
- @observe 装饰器在函数执行时才调用 get_client()；若进程中没有任何已初始化的
  Langfuse client（未注册到 LangfuseResourceManager._instances），get_client()
  会跳过追踪并打印 "Skipping tracing for decorated function"。
- 因此本模块在 import 时主动创建并注册一个全局 Langfuse client，确保 @observe
  在任意进程（后端 / MCP Server）都能读取到密钥配置。
"""
import os

from common.config import langfuse_config

_handler = None
_client_initialized = False


def _init_global_client():
    """模块加载时初始化并注册全局 Langfuse client（@observe 依赖它）。"""
    global _client_initialized
    if _client_initialized:
        return
    _client_initialized = True

    try:
        from langfuse import Langfuse
    except ImportError:
        # langfuse 未安装：@observe 降级为 no-op，不追踪
        return

    try:
        cfg = langfuse_config()
        if not cfg:
            # 未配置 LANGFUSE_* 变量：降级为无追踪模式，不影响核心业务
            return
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", cfg["public_key"])
        os.environ.setdefault("LANGFUSE_SECRET_KEY", cfg["secret_key"])
        os.environ.setdefault("LANGFUSE_BASE_URL", cfg["base_url"])
        # ★ 显式传参创建并注册全局 client（否则 @observe 的 get_client() 找不到）
        #   timeout=3：单次上报请求最多阻塞 3 秒，避免云端慢时永久挂起
        #   flush_interval=30 / flush_at=100：降低自动 flush 频率，减少同步网络阻塞
        _langfuse_client = Langfuse(
            public_key=cfg["public_key"],
            secret_key=cfg["secret_key"],
            base_url=cfg["base_url"],
            timeout=3,
            flush_interval=30,
            flush_at=100,
        )
    except Exception:
        # Langfuse 初始化失败（如云端不可达）不抛异常，降级为无追踪
        pass


def get_langfuse_handler():
    """返回 Langfuse CallbackHandler（单例）；不可用时返回 None（降级，不影响核心功能）"""
    global _handler
    if _handler is None:
        try:
            _init_global_client()
            from langfuse.langchain import CallbackHandler
            cfg = langfuse_config()
            if not cfg:
                return None
            _handler = CallbackHandler(public_key=cfg["public_key"])
        except Exception:
            # Langfuse 不可用时降级，不抛异常
            return None
    return _handler


def get_langfuse_callbacks():
    """返回 callbacks 列表；Langfuse 不可用时返回 None（供 ChatOpenAI / invoke / astream_events 使用）"""
    handler = get_langfuse_handler()
    return [handler] if handler else None


# @observe 装饰器（langfuse 4.x 从顶层导出；未安装时降级为 no-op）
try:
    from langfuse import observe
except ImportError:
    def observe(*args, **kwargs):
        """langfuse 未安装时的 no-op 装饰器"""
        def decorator(fn):
            return fn
        return decorator


# ★ 模块导入时立即初始化全局 client，确保 @observe 在任意进程都能工作
_init_global_client()
