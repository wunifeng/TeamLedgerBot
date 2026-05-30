"""认证相关 API schema。"""
from pydantic import BaseModel

from app.schemas.member import MemberResponse


class LoginRequest(BaseModel):
    """PIN 登录请求体。"""
    member_name: str
    pin: str


class TokenResponse(BaseModel):
    """登录成功返回的 JWT Token 和成员信息。"""
    access_token: str
    token_type: str = "bearer"
    member: MemberResponse
