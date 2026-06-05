"""本地成员停用 HTTP 冒烟验证。"""
import asyncio
from pathlib import Path
import sys
import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import AsyncSessionLocal
from app.main import app
from app.models.member import Member
from app.services.auth_service import create_access_token


async def _create_member_rows() -> list[Member]:
    """创建隔离测试成员，避免清空本地业务数据。"""
    suffix = uuid.uuid4().hex[:8]
    rows = [
        Member(name=f"delete-test-admin-{suffix}", role="admin", is_admin=True),
        Member(name=f"delete-test-ordinary-{suffix}", role="member"),
        Member(name=f"delete-test-target-{suffix}", role="member"),
        Member(name=f"delete-test-protected-{suffix}", role="member"),
        Member(name=f"delete-test-inactive-{suffix}", role="member", is_active=False),
    ]
    async with AsyncSessionLocal() as session:
        session.add_all(rows)
        await session.commit()
        return rows


async def _cleanup_member_rows(rows: list[Member]) -> None:
    """清理本脚本创建的成员测试数据。"""
    ids = [row.id for row in rows]
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Member).where(Member.id.in_(ids)))
        await session.commit()


async def _is_member_active(member_id: uuid.UUID) -> bool:
    async with AsyncSessionLocal() as session:
        value = await session.scalar(select(Member.is_active).where(Member.id == member_id))
        assert value is not None, f"成员 {member_id} 应存在"
        return value


async def run() -> None:
    """验证成员停用权限、幂等性和默认列表过滤。"""
    rows = await _create_member_rows()
    admin, ordinary, target, protected, inactive = rows
    admin_headers = {"Authorization": f"Bearer {create_access_token(admin.id, True)}"}
    ordinary_headers = {"Authorization": f"Bearer {create_access_token(ordinary.id, False)}"}

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/members/{target.id}", headers=admin_headers)
            assert response.status_code == 204, response.text
            assert await _is_member_active(target.id) is False

            active = await client.get("/api/members")
            assert active.status_code == 200, active.text
            assert str(target.id) not in {row["id"] for row in active.json()}

            all_rows = await client.get("/api/members", params={"include_inactive": True})
            assert all_rows.status_code == 200, all_rows.text
            target_row = next(row for row in all_rows.json() if row["id"] == str(target.id))
            assert target_row["is_active"] is False

            repeat = await client.delete(f"/api/members/{target.id}", headers=admin_headers)
            assert repeat.status_code == 204, repeat.text

            inactive_repeat = await client.delete(f"/api/members/{inactive.id}", headers=admin_headers)
            assert inactive_repeat.status_code == 204, inactive_repeat.text

            forbidden = await client.delete(f"/api/members/{protected.id}", headers=ordinary_headers)
            assert forbidden.status_code == 403, forbidden.text
            assert await _is_member_active(protected.id) is True

            self_delete = await client.delete(f"/api/members/{admin.id}", headers=admin_headers)
            assert self_delete.status_code == 403, self_delete.text
            assert await _is_member_active(admin.id) is True

            missing = await client.delete(f"/api/members/{uuid.uuid4()}", headers=admin_headers)
            assert missing.status_code == 404, missing.text

            no_token = await client.delete(f"/api/members/{protected.id}")
            assert no_token.status_code == 401, no_token.text
    finally:
        await _cleanup_member_rows(rows)

    print("member delete smoke: ok")


if __name__ == "__main__":
    asyncio.run(run())
