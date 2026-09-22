from chat.dao import HistoryDao

# 查询对话的历史记录 --- 只查询当前登录用户和父节点 (parent_id=0)
def query_history_by_email(email):
    result = HistoryDao.query_history_by_id(email)
    # 定义保存数据的列表
    data_list = []
    # 处理数据为客户端需要的格式
    for item in result:
        # ★ 新增：支持 title 字段，有 title 用 title，否则用 question
        title = item.get("title")
        question = item.get("question")
        final_title = title if title else question

        data_list.append(
            {
                "id": item["history_id"],
                "title": final_title,
                "time": item["create_time"].strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    return {
        "code": 200,
        "msg": "查询成功",
        "data": data_list
    }


# 根据选择的历史对话id查询全部对话记录
def query_history_all_by_id(history_id):
    result = HistoryDao.query_history_all_by_id(history_id)
    data_list = []
    for item in result:
        data_list.append(
            {
                "role": "user",
                "content": item["question"]
            }
        )
        data_list.append(
            {
                "role": "assistant",
                "content": item["answer"]
            }
        )
    return {
        "code": 200,
        "msg": "查询成功",
        "data": data_list
    }



# ★ 新增：获取历史消息列表（纯数据格式，供 ChatController 拼接上下文使用）
# ★ 改进：增加窗口限制，只保留最近 N 轮对话
MAX_HISTORY_EXCHANGES = 5

def get_history_messages(history_id, max_exchanges=MAX_HISTORY_EXCHANGES):
    """
    根据 history_id 查询该会话的所有历史消息，返回纯消息列表。
    返回格式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    最多返回最近 max_exchanges 轮对话（控制 token 消耗）。
    """
    if history_id <= 0:
        return []
    result = HistoryDao.query_history_all_by_id(history_id)
    messages = []
    for item in result:
        messages.append({"role": "user", "content": item["question"]})
        messages.append({"role": "assistant", "content": item["answer"]})

    # ★ 只保留最近 N 轮（每轮 = 1 user + 1 assistant）
    if len(messages) > max_exchanges * 2:
        messages = messages[-max_exchanges * 2:]

    return messages


# 保存对话结果
def save_chat_result(question, answer, parent_id, email):
    history_id = HistoryDao.save_chat_result(question, answer, parent_id, email)
    if history_id:
        return {
            "code": 200,
            "msg": "保存成功",
            "data": {"history_id": history_id}
        }
    return {
        "code": 500,
        "msg": "保存失败"
    }

# 根据邮箱和关键词搜索历史记录
def search_history_by_email_and_keyword(email, keyword):
    # 调用 Dao 层的新函数
    result = HistoryDao.search_history_by_email_and_keyword(email, keyword)

    # 处理数据为客户端需要的格式
    data_list = []
    for item in result:
        # ★ 新增：支持 title 字段
        title = item.get("title")
        question = item.get("question")
        final_title = title if title else question

        data_list.append(
            {
                "id": item["history_id"],
                "title": final_title,
                "time": item["create_time"].strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    return {
        "code": 200,
        "msg": "查询成功",
        "data": data_list
    }


#新增功能：处理删除历史记录的逻辑

# ===== ★ 新增：删除历史记录 =====
def delete_history_record(history_id):
    if not history_id:
        return {"code": 400, "msg": "ID不能为空"}

    success = HistoryDao.delete_history_record(history_id)

    if success:
        return {"code": 200, "msg": "删除成功"}
    else:
        return {"code": 500, "msg": "删除失败，请重试"}


# ===== ★ 新增：重命名对话标题 =====
def update_history_title(history_id, new_title):
    if not history_id or not new_title:
        return {"code": 400, "msg": "ID或标题不能为空"}

    affected = HistoryDao.update_history_title(history_id, new_title)

    if affected > 0:
        return {"code": 200, "msg": "标题更新成功"}
    elif affected == 0:
        return {"code": 404, "msg": "未找到对应对话记录"}
    else:
        return {"code": 500, "msg": "标题更新失败，请重试"}


if __name__ == '__main__':
    print(query_history_by_email("test@example.com"))
