from chat.utils.ChatUtil import ChatUtil

# 非流式输出 --- 非agent
def chat_no_agent(question):
    result = ChatUtil.chat(question)
    return {
        "code": 200,
        "msg": "success",
        "data": result
    }

# 流式输出 --- 非agent
def chat_no_agent_stream(question):
    # 获取结果
    result = ChatUtil.chat(question)
    # 返回结果
    return result