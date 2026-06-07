"""本地 PostgreSQL HTTP API 冒烟验证。"""
import asyncio
import uuid
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update

from app.database import AsyncSessionLocal
from app.main import app
from app.models.member import Member
from app.services import telegram_service
from app.services.auth_service import create_access_token


async def _ignore_telegram(_: str) -> None:
    """HTTP 冒烟验证不向真实群组发送消息。"""


async def run() -> None:
    """按网页调用顺序验证关键 HTTP 接口。"""

    telegram_service._send = _ignore_telegram
    async with AsyncSessionLocal() as session:
        await session.execute(text(
            "TRUNCATE bankroll_entries, salary_payments, salary_settlements, member_expenses, "
            "salary_accruals, daily_flow_reports, venues, categories, members CASCADE"
        ))
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        member = (await client.post("/api/members", json={"name": "敏", "role": "成员"})).json()
        ordinary = (await client.post("/api/members", json={"name": "普通成员", "role": "成员"})).json()
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Member)
                .where(Member.id == uuid.UUID(member["id"]))
                .values(is_admin=True)
            )
            await session.commit()
        admin_headers = {"Authorization": f"Bearer {create_access_token(uuid.UUID(member['id']), True)}"}
        ordinary_headers = {"Authorization": f"Bearer {create_access_token(uuid.UUID(ordinary['id']), False)}"}
        category = (await client.post("/api/categories", json={"name": "餐饮费", "type": "expense"})).json()
        venue = (await client.post("/api/venues", json={"name": "Otium", "rebate_rate": 0.2})).json()

        bankroll_initial = await client.post(
            "/api/bankroll/entries",
            json={
                "business_date": "2026-01-01",
                "member_id": member["id"],
                "entry_type": "initial",
                "amount": "1000",
            },
            headers=admin_headers,
        )
        assert bankroll_initial.status_code == 201, bankroll_initial.text
        assert Decimal(str(bankroll_initial.json()["signed_amount"])) == Decimal("1000.00")
        duplicate_initial = await client.post(
            "/api/bankroll/entries",
            json={
                "business_date": "2026-01-01",
                "member_id": member["id"],
                "entry_type": "initial",
                "amount": "100",
            },
            headers=admin_headers,
        )
        assert duplicate_initial.status_code == 422, duplicate_initial.text
        bankroll_top_up = await client.post(
            "/api/bankroll/entries",
            json={
                "business_date": "2026-01-02",
                "member_id": member["id"],
                "entry_type": "top_up",
                "amount": "500",
            },
            headers=admin_headers,
        )
        assert bankroll_top_up.status_code == 201, bankroll_top_up.text
        bankroll_return = await client.post(
            "/api/bankroll/entries",
            json={
                "business_date": "2026-01-03",
                "member_id": member["id"],
                "entry_type": "return",
                "amount": "200",
            },
            headers=admin_headers,
        )
        assert bankroll_return.status_code == 201, bankroll_return.text
        excessive_return = await client.post(
            "/api/bankroll/entries",
            json={
                "business_date": "2026-01-03",
                "member_id": member["id"],
                "entry_type": "return",
                "amount": "2000",
            },
            headers=admin_headers,
        )
        assert excessive_return.status_code == 422, excessive_return.text
        negative_adjustment = await client.post(
            "/api/bankroll/entries",
            json={
                "business_date": "2026-01-04",
                "member_id": member["id"],
                "entry_type": "adjustment",
                "amount": "1500",
                "adjustment_direction": "decrease",
                "remark": "盘点差异",
            },
            headers=admin_headers,
        )
        assert negative_adjustment.status_code == 201, negative_adjustment.text
        forbidden_bankroll_create = await client.post(
            "/api/bankroll/entries",
            json={
                "business_date": "2026-01-04",
                "member_id": ordinary["id"],
                "entry_type": "top_up",
                "amount": "100",
            },
            headers=ordinary_headers,
        )
        assert forbidden_bankroll_create.status_code == 403, forbidden_bankroll_create.text
        forbidden_bankroll_read = await client.get(
            "/api/bankroll/entries",
            params={"member_id": member["id"]},
            headers=ordinary_headers,
        )
        assert forbidden_bankroll_read.status_code == 403, forbidden_bankroll_read.text
        ordinary_summary = await client.get("/api/bankroll/summary", headers=ordinary_headers)
        assert ordinary_summary.status_code == 200, ordinary_summary.text
        assert [item["member_id"] for item in ordinary_summary.json()["items"]] == [ordinary["id"]]
        void_top_up = await client.post(
            f"/api/bankroll/entries/{bankroll_top_up.json()['id']}/void",
            json={"reason": "补充金额登记错误"},
            headers=admin_headers,
        )
        assert void_top_up.status_code == 200, void_top_up.text
        duplicate_void_bankroll = await client.post(
            f"/api/bankroll/entries/{bankroll_top_up.json()['id']}/void",
            json={"reason": "重复作废"},
            headers=admin_headers,
        )
        assert duplicate_void_bankroll.status_code == 422, duplicate_void_bankroll.text
        bankroll_summary = await client.get("/api/bankroll/summary", headers=admin_headers)
        assert bankroll_summary.status_code == 200, bankroll_summary.text
        admin_balance = next(
            item for item in bankroll_summary.json()["items"]
            if item["member_id"] == member["id"]
        )
        assert Decimal(str(admin_balance["balance"])) == Decimal("-700.00")
        active_bankroll_entries = await client.get(
            "/api/bankroll/entries",
            params={"member_id": member["id"]},
            headers=admin_headers,
        )
        assert active_bankroll_entries.status_code == 200, active_bankroll_entries.text
        assert active_bankroll_entries.json()["total"] == 3
        all_bankroll_entries = await client.get(
            "/api/bankroll/entries",
            params={"member_id": member["id"], "include_voided": True},
            headers=admin_headers,
        )
        assert all_bankroll_entries.status_code == 200, all_bankroll_entries.text
        assert all_bankroll_entries.json()["total"] == 4

        flow_payload = {
            "business_date": "2026-01-30",
            "member_id": member["id"],
            "venue_id": venue["id"],
            "game": "俄罗斯",
            "card_number": "0",
            "principal": 1500,
            "chip_code": 0,
            "loss_rebate": 300,
            "profit_loss": -1200,
        }
        response = await client.post("/api/flows", json=flow_payload, headers=admin_headers)
        assert response.status_code == 201, response.text
        assert response.json()["salary_amount"] == "15"
        assert (await client.post("/api/flows", json=flow_payload, headers=admin_headers)).status_code == 409
        assert (await client.post("/api/flows", json={**flow_payload, "business_date": "2026-01-31", "profit_loss": -1199}, headers=admin_headers)).status_code == 422

        expense = await client.post(
            "/api/expenses",
            data={
                "business_date": "2026-01-30",
                "member_id": member["id"],
                "category_id": category["id"],
                "amount": "120",
                "remark": "团队晚餐",
            },
            files={"receipt": ("receipt.png", b"local-test-receipt", "image/png")},
            headers=admin_headers,
        )
        assert expense.status_code == 201, expense.text
        expense_body = expense.json()
        assert expense_body["receipt_url"].startswith("/uploads/")
        assert (await client.patch(f"/api/expenses/{expense_body['id']}/reimbursed", json={"reimbursed": True}, headers=admin_headers)).status_code == 200

        settlements = await client.get("/api/salary/settlements", params={"period_start": "2026-01-01", "period_end": "2026-01-31"})
        assert settlements.status_code == 200, settlements.text
        settlement = next(
            item for item in settlements.json()["items"]
            if item["member_id"] == member["id"]
        )
        assert settlement["payable_amount"] == "15.00"
        forbidden = await client.post(f"/api/salary/settlements/{settlement['id']}/pay", json={"amount": 1}, headers=ordinary_headers)
        assert forbidden.status_code == 403, forbidden.text
        payment = await client.post(f"/api/salary/settlements/{settlement['id']}/pay", json={"amount": 10}, headers=admin_headers)
        assert payment.status_code == 201, payment.text
        payment_body = payment.json()
        assert payment_body["settlement"]["unpaid_amount"] == "5.00"
        assert len(payment_body["settlement"]["payments"]) == 1
        assert (await client.post(f"/api/salary/settlements/{settlement['id']}/pay", json={"amount": 6}, headers=admin_headers)).status_code == 422

        void_forbidden = await client.post(
            f"/api/salary/payments/{payment_body['payment']['id']}/void",
            json={"reason": "普通成员无权作废"},
            headers=ordinary_headers,
        )
        assert void_forbidden.status_code == 403, void_forbidden.text
        voided = await client.post(
            f"/api/salary/payments/{payment_body['payment']['id']}/void",
            json={"reason": "金额登记错误"},
            headers=admin_headers,
        )
        assert voided.status_code == 200, voided.text
        assert voided.json()["settlement"]["paid_amount"] == "0.00"
        assert voided.json()["settlement"]["unpaid_amount"] == "15.00"
        assert voided.json()["payment"]["voided_at"] is not None
        duplicate_void = await client.post(
            f"/api/salary/payments/{payment_body['payment']['id']}/void",
            json={"reason": "重复作废"},
            headers=admin_headers,
        )
        assert duplicate_void.status_code == 422, duplicate_void.text

        summary = (await client.get("/api/dashboard/summary")).json()
        assert summary["total_profit_loss"] == "-1200.00"
        assert summary["net_result"] == "-1335.00"

    print("api smoke: ok")


if __name__ == "__main__":
    asyncio.run(run())
