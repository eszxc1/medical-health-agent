"""
Langfuse 全链路追踪上报测试
============================
用法：
    cd rag_server
    python scripts/test_langfuse.py

验证：运行后登录 Langfuse 面板，应能看到名为 "langfuse-test" 的 trace。
"""
import os
import sys

# 让 scripts/ 下直接运行时能 import common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.config import langfuse_config

# 触发 Fail Fast 校验 + 显式设置环境变量（供 @observe / CallbackHandler 读取）
cfg = langfuse_config()
os.environ["LANGFUSE_PUBLIC_KEY"] = cfg["public_key"]
os.environ["LANGFUSE_SECRET_KEY"] = cfg["secret_key"]
os.environ["LANGFUSE_BASE_URL"] = cfg["base_url"]

from langfuse import observe


@observe(name="langfuse-test", as_type="span")
def hello(name: str) -> str:
    return f"hello {name}"


if __name__ == "__main__":
    result = hello("world")
    print("[observe] result:", result)

    from langfuse import get_client
    get_client().flush()
    print("[langfuse] 已 flush，请到 Langfuse 面板确认 'langfuse-test' trace 是否上报成功")
