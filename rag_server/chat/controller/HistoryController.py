from fastapi import APIRouter

from chat.service import HistoryService
from entity.HistoryInfo import HistoryInfo
history_router = APIRouter()

# 查询对话的历史记录 --- 只查询当前登录用户和父节点 (parent_id=0)
@history_router.get("/queryHistoryByEmail")
def query_history_by_email(email):
    return HistoryService.query_history_by_email(email)

# 根据选择的历史对话id查询全部对话记录
@history_router.get("/queryHistoryAllById")
def query_history_all_by_id(historyId: int):
    return HistoryService.query_history_all_by_id(historyId)




# 根据邮箱和关键词搜索历史记录
@history_router.get("/searchHistory")
def search_history(email: str, keyword: str):
    return HistoryService.search_history_by_email_and_keyword(email, keyword)
# ===== 新增：保存对话 =====
# 保存对话结果

@history_router.post("/saveChatResult")
def save_chat_result(historyInfo: HistoryInfo):
    return HistoryService.save_chat_result(historyInfo.question, historyInfo.answer, historyInfo.parentId, historyInfo.email)


# ===== ★ 新增：删除历史记录 =====
@history_router.post("/deleteHistory")
def delete_history(history_id: int):
    return HistoryService.delete_history_record(history_id)


# ===== ★ 新增：重命名对话标题 =====
@history_router.post("/updateHistoryTitle")
def update_history_title(history_id: int, new_title: str):
    return HistoryService.update_history_title(history_id, new_title)