
from pydantic import BaseModel

class HistoryInfo(BaseModel):
    question: str
    answer: str
    parentId: int
    email: str