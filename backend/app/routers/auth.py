"""认证路由：登录、查看当前成员、设置 PIN。"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.member import Member
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.member import MemberResponse, MemberSetPin
from app.services import auth_service

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="成员 PIN 登录",
    description="通过成员名和 PIN 登录，返回 JWT Token。",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    member, token = await auth_service.login_by_name_and_pin(db, data.member_name, data.pin)
    return TokenResponse(
        access_token=token,
        member=MemberResponse.model_validate(member),
    )


@router.get(
    "/me",
    response_model=MemberResponse,
    summary="获取当前登录成员信息",
)
async def get_me(
    current_member: Member = Depends(auth_service.get_current_member),
) -> MemberResponse:
    return MemberResponse.model_validate(current_member)


@router.post(
    "/set-pin",
    status_code=204,
    summary="设置/重置成员 PIN",
    description="管理员可设置任何人的 PIN，普通成员只能设置自己的。",
)
async def set_pin(
    data: MemberSetPin,
    current_member: Member = Depends(auth_service.get_current_member),
    db: AsyncSession = Depends(get_db),
) -> None:
    await auth_service.set_member_pin(db, data.member_id, data.pin, current_member)
