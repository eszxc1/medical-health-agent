import asyncio
import os
import sys
from fastmcp import Client
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ★ 调试入口兼容：直接运行 `python mymcp/MCPClient.py` 时，sys.path[0] 是 mymcp/，
#   手动把父目录 rag_server/ 加入 sys.path，确保能 import common.config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.config import env

MCP_SERVER_URL = env("MCP_SERVER_URL", "http://localhost:9000/mcp")
def call_mcp_tool(tool_name, **kwargs):
    async def _call():
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool(tool_name, kwargs)
            return _extract_result(result)
    return asyncio.run(_call())


def _extract_result(result):
    """
    ★ 修复 1：从 fastmcp 的 CallToolResult 中提取干净的结构化数据。

    为什么？—— client.call_tool 返回的是 CallToolResult（Pydantic 对象），
    直接返回给 LangChain 会被 str() 成冗长的 repr（CallToolResult(content=[TextContent(...)], ...)），
    LLM 被迫从噪音里挖掘真实结果，容易读错 → 导致"瞎编操作成功"。

    提取策略：
    1. 优先取 result.data（结构化 dict/JSON，如 {"result": "已添加过敏史: 青霉素"}）
    2. 其次取 result.content[0].text（纯文本内容）
    3. 兜底原样返回（兼容某些版本 call_tool 直接返回 dict/str 的情况）
    """
    # 1) 结构化数据
    data = getattr(result, "data", None)
    if data is not None:
        return data
    # 2) 内容块里的纯文本
    content = getattr(result, "content", None)
    if content:
        first = content[0] if isinstance(content, (list, tuple)) else content
        text = getattr(first, "text", None)
        if text is not None:
            return text
    # 3) 兜底：原样返回
    return result


if __name__ == '__main__':
    data= call_mcp_tool(tool_name="send_email", receiver="test@example.com")
    print (data)


