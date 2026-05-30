"""认证服务：PIN 验证、JWT 签发与解析、FastAPI 依赖注入。"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.member import Member

_bearer = HTTPBearer(auto_error=False)


# ── PIN 哈希工具 ──────────────────────────────────────────────────────────────

def hash_pin(pin: str) -> str:
    """将明文 PIN 哈希为 bcrypt 字符串。"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pin.encode(), salt).decode()


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """验证明文 PIN 与哈希是否匹配。"""
    try:
        return bcrypt.checkpw(plain_pin.encode(), hashed_pin.encode())
    except ValueError:
        return False



# ── JWT 工具 ──────────────────────────────────────────────────────────────────

def create_access_token(member_id: uuid.UUID, is_admin: bool) -> str:
    """签发 JWT Token，有效期由配置决定。"""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(member_id),
        "is_admin": is_admin,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    """解析 JWT Token，失败抛 401。"""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI 依赖 ──────────────────────────────────────────────────────────────

async def get_current_member(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Member:
    """从 Bearer Token 中解析当前登录成员，不存在时抛 401。"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_token(credentials.credentials)
    member_id_str = payload.get("sub")
    if not member_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 格式错误")

    member = await db.get(Member, uuid.UUID(member_id_str))
    if member is None or not member.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="成员不存在或已停用，请重新登录",
        )
    return member


# ── 业务逻辑 ──────────────────────────────────────────────────────────────────

async def login_by_name_and_pin(
    session: AsyncSession, member_name: str, pin: str
) -> tuple[Member, str]:
    """按名字查找成员并验证 PIN，返回 (member, token)。"""
    result = await session.execute(
        select(Member).where(Member.name == member_name, Member.is_active.is_(True))
    )
    member = result.scalar_one_or_none()

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="成员不存在或已停用",
        )
    if not member.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="该成员尚未设置 PIN，请联系管理员",
        )
    if not verify_pin(pin, member.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN 错误",
        )
    token = create_access_token(member.id, member.is_admin)
    return member, token


async def set_member_pin(
    session: AsyncSession,
    target_member_id: uuid.UUID,
    new_pin: str,
    operator: Member,
) -> None:
    """设置或重置成员 PIN。管理员可设置任何人，普通成员只能设置自己。"""
    if not operator.is_admin and operator.id != target_member_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限：只有管理员才能设置他人的 PIN",
        )
    target = await session.get(Member, target_member_id)
    if target is None or not target.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")
    target.pin_hash = hash_pin(new_pin)
    await session.flush()
