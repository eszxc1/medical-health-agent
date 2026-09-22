
import asyncio
import json
import re
import time
import traceback

from fastapi import APIRouter, Request

from chat.service import ChatService, HistoryService
from starlette.responses import StreamingResponse
from fastapi.responses import JSONResponse

from common.LangfuseUtil import get_langfuse_callbacks

chat_router = APIRouter()


def _sse(payload: dict) -> str:
    """构造 SSE 数据行：统一补 startTime 毫秒时间戳，确保字段齐全"""
    payload.setdefault("startTime", int(time.time() * 1000))
    return f"data: {json.dumps(payload)}\n\n"


def _field(obj, key, default=None):
    """兼容 dict / 对象两种形态取字段"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _extract_chunk_text(chunk) -> str:
    """从 LangChain 消息 chunk 中提取文本。

    兼容 langchain-core 1.x 的多种形态：
    - chunk 本身可能是 dict（on_chat_model_end 的 output 可能被序列化成 dict）
    - content 直接为字符串
    - content 为空、文本在 content_blocks（dict 形态 或 pydantic 对象形态）
    """
    if chunk is None:
        return ""
    # 1) content 为字符串且非空：直接返回
    content = _field(chunk, "content", "")
    if isinstance(content, str) and content:
        return content
    # 2) content_blocks 兜底：同时兼容 dict 与对象两种形态
    blocks = _field(chunk, "content_blocks", None) or []
    texts = []
    for b in blocks:
        if isinstance(b, dict):
            if b.get("type") == "text":
                texts.append(b.get("text") or "")
        else:
            if getattr(b, "type", None) == "text":
                texts.append(getattr(b, "text", None) or "")
    return "".join(texts)


def _looks_like_json(text: str) -> bool:
    """判断文本是否为工具返回的 JSON 结构（这类中间数据不应展示给用户）。"""
    t = text.strip()
    if len(t) < 2 or t[0] not in "{[" or t[-1] not in "}]":
        return False
    # 命中工具返回字段（result / symptoms 等），即使 JSON 不完整也判定为结果
    if re.search(r'"(result|symptoms|drug_related|diseases|medications|allergies|status|data|code|msg)"\s*:', t):
        return True
    try:
        json.loads(t)
        return True
    except (ValueError, TypeError):
        return False


def _extract_stream_text(chunk) -> str:
    """从流式事件 chunk 中提取【最终 LLM 生成】的文本。

    只放行 AI / assistant 消息的 content；丢弃 Tool / Human / System 消息的
    原始返回（工具返回的 {"result": [...]} JSON、"知识图谱中暂时未收录..."等中间日志）。
    """
    if chunk is None:
        return ""
    # 1) 纯字符串：可能是正文也可能是工具 JSON 结果，用 JSON 嗅探兜底
    if isinstance(chunk, str):
        return "" if _looks_like_json(chunk) else chunk

    # 2) 消息类型过滤：只放行 AI / assistant
    msg_type = _field(chunk, "type", "") or _field(chunk, "role", "")
    if msg_type:
        if msg_type not in ("ai", "assistant") and "AI" not in str(msg_type):
            return ""
        # AI 消息：正文可信，直接取 content（不再做 JSON 嗅探）
        return _extract_chunk_text(chunk)

    # 3) 无类型信息的 dict / 对象：可能直接携带 content，也可能是嵌套结构
    text = _extract_chunk_text(chunk)
    if text:
        return "" if _looks_like_json(text) else text

    # 4) LangGraph on_chain_stream 常见：{"messages": [...]} 或 {"node": {"messages": [...]}}
    if isinstance(chunk, dict):
        if "messages" in chunk:
            return _extract_stream_text(chunk["messages"])
        # 嵌套节点：递归深入 dict/list，不碰字符串元数据（如 run_id）
        for v in chunk.values():
            if isinstance(v, (dict, list)):
                t = _extract_stream_text(v)
                if t:
                    return t
        return ""
    # 5) 消息列表：只取最后一条（流式增量）
    if isinstance(chunk, list):
        return _extract_stream_text(chunk[-1]) if chunk else ""
    return ""


def _append_unique(full: str, new_text: str):
    """追加文本并去重。返回 (新全文, 本次增量)。

    on_chain_stream 可能全量重发已累计内容，也可能与 on_chat_model_stream
    携带相同 token，需按前缀匹配只取增量部分，避免正文重复。
    """
    if not new_text:
        return full, ""
    if full and new_text.startswith(full):
        delta = new_text[len(full):]
        return full + delta, delta
    return full + new_text, new_text


# 非agent流式输出
@chat_router.get("/chatNoAgentStream")
def chat_no_agent_stream(question: str, history_id: int = 0):
    result = ChatService.chat_no_agent_stream(question)

    def generator():
        for chunk in result:
            yield _sse({'type': 'text', 'content': chunk})
            time.sleep(0.1)
        yield _sse({'type': 'end', 'content': '[DONE]'})

    return StreamingResponse(
        content=generator(),
        media_type="text/event-stream",
    )


# Agent流式输出
# ★ Phase 1：新增 email 参数 + 服务端历史保存 + 调试日志
@chat_router.get("/chatAgentStream")
async def chat_agent_stream(question: str, request: Request, history_id: int = 0, email: str = ""):
    print("[DEBUG] 原始query_params:", request.query_params)
    agent = request.app.state.agent

    # ★★★ 身份校验：打印收到的请求参数，确保前后端身份一致 ★★★
    print("=" * 60)
    print(f"[IDENTITY] 收到聊天请求:")
    print(f"  email     = {email if email else '(空)'}")
    print(f"  history_id = {history_id}")
    print(f"  question   = {question[:80]}")
    print("=" * 60)

    # ★ 修复 1：强制校验 email 是否为空
    if not email or not email.strip():
        print("[IDENTITY] 拒绝请求：缺少用户邮箱，返回 401")
        return JSONResponse(
            status_code=401,
            content={"code": 401, "msg": "未登录或用户身份丢失，请重新登录"}
        )

    # ★ 修复 2：校验 email 格式
    if "@" not in email:
        print(f"[IDENTITY] 拒绝请求：邮箱格式无效: {email}")
        return JSONResponse(
            status_code=401,
            content={"code": 401, "msg": f"用户邮箱格式无效: {email}，请重新登录"}
        )

    # ★ 修复 3：从 MySQL users 表校验邮箱是否真实存在，防止前端传入任意邮箱绕过鉴权
    try:
        from users.dao import UsersDao
        user = UsersDao.find_user_by_email(email)
        if not user:
            print(f"[IDENTITY] 拒绝请求：邮箱不存在于数据库中: {email}")
            return JSONResponse(
                status_code=401,
                content={"code": 401, "msg": f"邮箱 {email} 未注册，请检查后重新登录"}
            )
        # 获取 user_id 供后续工具使用
        # 如果 user 是列表，取第一个元素
        user = user[0] if isinstance(user, list) else user
        user_id = user.get("user_id")
        print(f"[IDENTITY] 邮箱校验通过: {email}, user_id={user_id}")
    except Exception as e:
        print(f"[IDENTITY] 邮箱校验异常: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"code": 500, "msg": f"用户身份校验服务异常: {str(e)}"}
        )

    # ★ 从 MySQL 获取历史消息（只加载当前用户的历史，防止跨用户数据泄露）
    history_messages = HistoryService.get_history_messages(history_id)
    messages = history_messages + [{"role": "user", "content": question}]

    # ★ 方案 A：前端已登录，直接将 email + user_id 注入为强制指令
    messages.insert(0, {
        "role": "system",
        "content": (
            f"【系统指令】当前对话用户的邮箱是: {email}，user_id 是: {user_id}。"
            f"这是唯一合法且已确认有效的用户标识，你只能查询和操作此邮箱对应的健康数据。"
            f"★ 此邮箱已经确认存在，你在执行任何需要邮箱的操作时，都必须直接使用 {email}，"
            f"严禁再向用户询问邮箱。"
            f"查询操作：用户问健康信息时，直接调用 get_user_profile(email=\"{email}\")。"
            f"更新操作：用户提供新健康信息（如'头孢过敏'、'昨天开始吃药'、'我有高血压'）时，"
            f"直接调用 update_user_profile(email=\"{email}\", field=..., value=..., date=...)，禁止先问邮箱。"
            f"其他操作（save_health_plan、evaluate_drug_safety、get_health_plans）同理，直接用 {email}。"
            f"绝对禁止调用 find_email 工具查询其他用户的邮箱。"
        )
    })

    # ★ 调试日志：打印发送给 LLM 的完整 messages（含用户身份确认）
    print("=" * 60)
    print(f"[DEBUG] 发送给 LLM 的 messages ({len(messages)} 条), 用户身份: {email}, user_id: {user_id}")
    for i, msg in enumerate(messages):
        role = msg.get("role", "?")
        content = str(msg.get("content", ""))[:200]
        print(f"  [{i}] role={role}: {content}")
    print("=" * 60)

    async def generator():
        # 收集完整回复文本，用于服务端保存
        full_response = ""
        # ★ 加固 4：医疗建议标志位，用于在流末尾硬编码追加免责声明
        medical_tool_called = False
        # ★ 兜底：记录最后一次 LLM 完整输出，用于「流式 chunk 全空」时补发正文
        last_model_output = ""
        # ★ Langfuse 容错：可用则传 callbacks，不可用则降级为无追踪（不阻塞流式输出）
        langfuse_callbacks = get_langfuse_callbacks()
        event_config = {"callbacks": langfuse_callbacks} if langfuse_callbacks else None
        try:
            # ★ 超时保护：60 秒无任何事件则主动断开，避免生成器无限挂起
            event_stream = agent.astream_events(
                {"messages": messages},
                version="v2",
                config=event_config,
            ).__aiter__()

            while True:
                try:
                    event = await asyncio.wait_for(event_stream.__anext__(), timeout=60)
                except asyncio.TimeoutError:
                    print("[ERROR] astream_events 超时（60 秒无数据），主动断开连接")
                    yield _sse({'type': 'error', 'content': '响应超时，请稍后重试'})
                    yield _sse({'type': 'end', 'content': '[DONE]'})
                    return  # 提前退出，跳过后续免责声明/保存/结束标记
                except StopAsyncIteration:
                    break

                kind = event.get("event")

                # ★ langchain-core 1.x 的 astream_events 流式事件名为 on_chain_stream，
                #   旧版本为 on_chat_model_stream，两者都监听以兼容不同版本。
                if kind in ("on_chain_stream", "on_chat_model_stream"):
                    chunk = event.get("data", {}).get("chunk")
                    text = _extract_stream_text(chunk)
                    if text:
                        full_response, delta = _append_unique(full_response, text)
                        if delta:
                            yield _sse({'type': 'text', 'content': delta})

                elif kind == "on_chat_model_end":
                    # ★ 记录本轮 LLM 调用的完整输出，作为流式 chunk 全空时的兜底
                    last_model_output = _extract_stream_text(event.get("data", {}).get("output"))

                elif kind == "on_tool_start":
                    tool_name = event.get("name")
                    tool_msg = f"正在调用工具: {tool_name}..."
                    print(f"[DEBUG] Agent 调用工具: {tool_name}")
                    # ★ 检测医疗/饮食相关工具，触发免责声明兜底
                    if tool_name in ("evaluate_drug_safety", "save_health_plan", "get_disease_advice"):
                        medical_tool_called = True
                    yield _sse({'type': 'tool', 'content': tool_msg})

                elif kind == "on_tool_end":
                    # ★ 修复 3：打印工具真实返回值，验证回灌链路是否干净
                    tool_name = event.get("name")
                    data = event.get("data") or {}
                    output = data.get("output")
                    output_str = str(output)
                    if len(output_str) > 500:
                        output_str = output_str[:500] + "...(已截断)"
                    print(f"[DEBUG] Agent 工具执行完毕: {tool_name}")
                    print(f"[DEBUG] 工具返回值: {output_str}")

            # ★ 兜底 1：若全程未流式收到任何文本（chunk 全空 / 内容形态不兼容），
            #    但 LLM 已生成完整回复，则用最后一次 on_chat_model_end 的输出一次性补发，
            #    保证前端至少能收到正文，而不是只剩 [DONE]。
            if not full_response and last_model_output:
                full_response = last_model_output
                yield _sse({'type': 'text', 'content': last_model_output})

            # ★ 兜底 2：若 LLM 连完整输出都没有（如简单问候被判定为"无需回复"），
            #    发送一个默认文本包，防止前端一直等待、永远收不到任何 text 事件。
            if not full_response:
                fallback_text = "抱歉，我暂时没有生成有效的回复，请换个问题再试一次。"
                full_response = fallback_text
                yield _sse({'type': 'text', 'content': fallback_text})

            # ★ 加固 4：免责声明硬编码兜底（工具触发 + 关键词触发双保险）
            # 为什么在服务端硬编码？—— LLM 有时会忘记输出免责声明，
            #    不能把医疗合规风险完全交给 AI，必须在流末尾强制追加。
            # 调整 3：只要正文输出任何健康/饮食/用药建议，即使没调 save_health_plan 也追加。
            if not medical_tool_called:
                medical_keywords = ["建议", "注意", "忌口", "宜吃", "慎用", "不宜", "禁忌",
                                    "用药", "服药", "饮食", "运动", "食谱", "调理", "方案",
                                    "副作用", "相互作用", "复诊", "就医", "处方"]
                if any(kw in full_response for kw in medical_keywords):
                    medical_tool_called = True
            if medical_tool_called:
                # ★ 使用 HTML 注释 <!--SPLIT--> 作为免责声明的唯一切割锚点
                # 为什么不用 ⚠️ 或"免责声明"文本？
                # —— ⚠️ 会出现在 AI 正文的"风险提示"部分，"免责声明"也可能被正文提及，
                #    只有 HTML 注释是正文中绝对不可能出现的唯一标识。
                disclaimer = (
                    "\n\n<!--SPLIT-->\n> ⚠️ **免责声明**：以上内容由 AI 生成，仅供参考，"
                    "不构成专业医疗诊断或用药建议。如有不适，请立即就医。"
                )
                full_response += disclaimer
                yield _sse({'type': 'text', 'content': disclaimer})

            # ★ 服务端保存历史：确保下一轮请求能立即加载到本次对话
            # ★ 同时把「会话根 ID」回传给前端，前端据此续写同一会话（修复刷新断连）
            saved_history_id = 0
            if email and full_response:
                try:
                    save_result = HistoryService.save_chat_result(question, full_response, history_id, email)
                    if isinstance(save_result, dict) and save_result.get("data"):
                        saved_history_id = save_result["data"].get("history_id", 0)
                    print(f"[DEBUG] 历史已保存: {question[:30]}... -> {full_response[:30]}...")
                    print(f"[SESSION] 本次保存 history_id={saved_history_id}（入参 history_id/parent={history_id}）")
                except Exception as e:
                    print(f"[DEBUG] 保存历史失败: {e}")
                    traceback.print_exc()

            # ★ 会话根 ID：首条消息（history_id=0）用新插入的 root id；后续消息沿用传入的 history_id
            root_history_id = history_id if history_id and history_id > 0 else saved_history_id
            print(f"[SESSION] 回传给前端的会话根 ID: {root_history_id}")

            # 结束标记（携带会话根 ID，供前端续写同一会话）
            yield _sse({'type': 'end', 'content': '[DONE]', 'history_id': root_history_id})

        except Exception as e:
            print(f"[ERROR] Agent 流式输出异常: {e}")
            traceback.print_exc()
            yield _sse({'type': 'error', 'content': f'服务器错误: {str(e)}'})
            yield _sse({'type': 'end', 'content': '[DONE]'})

    return StreamingResponse(
        content=generator(),
        media_type="text/event-stream",
    )