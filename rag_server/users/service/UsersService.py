
"""
这里的方法就是通过智能体agent对象来完成：基于配置LLM完成的
1、问题的识别 --- 拆解任务 --- 意图识别
2、判定是否需要调用工具
3、如果要调用工具，调用哪一个工具或哪几个工具
4、如果不需要调工具，直接通过LLM输出结果
"""

import json
import re
from common import ResponseUtil
from users.dao import UsersDao
from common.LangfuseUtil import get_langfuse_callbacks


def extract_json(content):
    """
    从 Agent 的响应文本中提取 JSON 对象。
    返回: 解析成功 → dict，解析失败 → None（让调用方继续尝试下一条消息）
    """
    if not content:
        return None
    # 策略 1: 直接解析整个文本为 JSON
    try:
        return json.loads(content)
    except:
        pass
    # 策略 2: 从 Markdown 代码块中提取 ```json ... ```
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    # 策略 3: 匹配文本中的第一个完整 JSON 对象（支持嵌套和跨行）
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    return None


def extract_agent_response(messages):
    """
    从 Agent 消息列表中提取最终响应。
    ★ 修复：只解析 AIMessage，排除 ToolMessage 的干扰。
    为什么？—— ToolMessage 包含工具返回的原始数据（如 find_email 返回的数据库查询结果），
    如果误解析 ToolMessage 中的 JSON，可能返回错误用户的邮箱，导致身份错乱。
    """
    from langchain_core.messages import AIMessage
    if not messages:
        return {"code": 500, "msg": "没有消息"}
    # 第一轮：只从 AIMessage 中解析 JSON（从后往前找）
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            result = extract_json(msg.content)
            if result:
                print(f"[IDENTITY] extract_agent_response: 从 AIMessage 解析成功 → {str(result)[:100]}")
                return result
    # 第二轮：取最后一条 AIMessage 的纯文本作为 msg
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            text = msg.content.strip()
            if text:
                print(f"[IDENTITY] extract_agent_response: 从 AIMessage 取纯文本 → {text[:100]}")
                return {"code": 200, "msg": text}
    return {"code": 500, "msg": "没有结果"}


# 邮箱登录
def send_email(username, agent):
    try:
        response = agent.invoke({
            "messages": [
                {"role": "user", "content": f"请帮我给用户{username}发送验证码"}
            ]
        }, {"configurable": {"thread_id": "auth_send_email"}, "callbacks": get_langfuse_callbacks()})
        result = extract_agent_response(response.get("messages", []))
        print(f"[IDENTITY] send_email: username={username} → 返回结果: {str(result)[:150]}")
        return result
    except Exception as e:
        return {"code": 500, "msg": f"发送邮件失败: {str(e)}"}


# 验证验证码
def verify_code(receiver, code, agent):
    try:
        response = agent.invoke({
            "messages": [
                {"role": "user", "content": f"验证验证码，邮箱号为{receiver}，验证码为{code}"}
            ]
        }, {"configurable": {"thread_id": "auth_verify_code"}, "callbacks": get_langfuse_callbacks()})
        return extract_agent_response(response.get("messages", []))
    except Exception as e:
        return {"code": 500, "msg": f"验证失败: {str(e)}"}


# 用户注册（不含密码）
def register(username, email):
    # 检查用户名是否已存在
    existing_user = UsersDao.find_user_by_username(username)
    if existing_user:
        return ResponseUtil.error("用户名已存在")

    # 检查邮箱是否已存在
    existing_email = UsersDao.find_user_by_email(email)
    if existing_email:
        return ResponseUtil.error("邮箱已被注册")

    # 插入新用户
    result = UsersDao.insert_user(username, email)
    if result:
        return ResponseUtil.success("注册成功")
    return ResponseUtil.error("注册失败")


# yllwyw 新增：注销用户，只使用 email 字段定位当前用户
def delete_account(email):
    existing_user = UsersDao.find_user_by_email(email)
    if not existing_user:
        return ResponseUtil.error("用户不存在")

    result = UsersDao.delete_user_by_email(email)
    if result:
        return ResponseUtil.success("账号已注销")
    return ResponseUtil.error("账号注销失败")
# yllwyw 新增结束