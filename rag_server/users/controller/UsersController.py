
# 配置子路由引入APIRouter
from urllib import request

from fastapi import APIRouter, Request

from users.service import UsersService

# 创建子路由实例
users_router = APIRouter()

# 发送邮件接口
@users_router.get("/sendEmail")
def send_email(username: str, request: Request):
    agent = request.app.state.agent
    return UsersService.send_email(username, agent)

# 验证验证码
@users_router.get("/verifyCode")
def verify_code(receiver: str, code: str, request: Request):
    agent = request.app.state.agent
    return UsersService.verify_code(receiver, code, agent)

# 注册接口（不含密码）
@users_router.post("/register")
def register(username: str, email: str):
    return UsersService.register(username, email)


# yllwyw 新增：用户注销接口
@users_router.delete("/deleteAccount")
def delete_account(email: str):
    return UsersService.delete_account(email)
# yllwyw 新增结束