import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

def response_util(response):
    # 调用模型后的响应结果是一个字典，我们需要提取的就是字典中最后一个AIMessage的content的内容 --- 响应结果
    messages = response.get("messages", [])
    if not messages:
        return {"code": 500, "msg": "没有消息"}
    # 存储AIMessage中的内容
    ai_content = []
    try:
        # 遍历messages，找到最后一个可解析为JSON的AIMessage
        for msg in messages:
            if isinstance(msg, AIMessage) and msg.content:
                try:
                    ai_content.append(json.loads(msg.content))
                except json.JSONDecodeError:
                    # 跳过非JSON的中间思考消息
                    continue
        # 输出结果 --- 只要最后一个AIMessage的content
        if not ai_content:
            return {"code": 500, "msg": "没有结果"}
        result = ai_content[-1]
        if result:
            return result
        return {"code": 500, "msg": "没有结果"}
    except Exception as e:
        return {"code": 500, "msg": str(e)}


# ★ 新增：统一成功响应
def success(msg="成功", data=None):
    return {
        "code": 200,
        "msg": msg,
        "data": data
    }


# ★ 新增：统一失败响应
def error(msg="失败", data=None):
    return {
        "code": 500,
        "msg": msg,
        "data": data
    }