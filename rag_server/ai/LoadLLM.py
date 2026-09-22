
from langchain_openai import ChatOpenAI

from common.config import env, required_env
from common.LangfuseUtil import get_langfuse_callbacks

def load_model():
    return ChatOpenAI(
        api_key=required_env("DASHSCOPE_API_KEY"),
        base_url=env("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model=env("LLM_MODEL", "qwen3.8-max-0902"),
        streaming=True,
        timeout=60,        # ★ 单次请求 60 秒超时，杜绝 LLM 网络不通时无限挂起
        max_retries=1,     # ★ 最多重试 1 次
        callbacks=get_langfuse_callbacks(),
    )