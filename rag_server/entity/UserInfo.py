from pydantic import BaseModel

class UserInfo(BaseModel):
    username: str
    email: str
    password: str = None