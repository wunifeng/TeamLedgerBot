"""本地 PostgreSQL HTTP API 冒烟验证。"""
import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.main import app
from app.services import telegram_service


async def _ignore_telegram(_: str) -> None:
    """HTTP 冒烟验证不向真实群组发送消息。"""


async def run() -> None:
    """按网页调用顺序验证关键 HTTP 接口。"""

    telegram_service._send = _ignore_telegram
    async with AsyncSessionLocal() as session:
        await session.execute(text(
            "TRUNCATE salary_payments, salary_settlements, member_expenses, "
            "salary_accruals, daily_flow_reports, venues, categories, members CASCADE"
        ))
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        member = (await client.post("/api/members", json={"name": "敏", "role": "成员"})).json()
        category = (await client.post("/api/categories", json={"name": "餐饮费", "type": "expense"})).json()
        venue = (await client.post("/api/venues", json={"name": "Otium", "rebate_rate": 0.2})).json()

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
        response = await client.post("/api/flows", json=flow_payload)
        assert response.status_code == 201, response.text
        assert response.json()["salary_amount"] == "15"
        assert (await client.post("/api/flows", json=flow_payload)).status_code == 409
        assert (await client.post("/api/flows", json={**flow_payload, "business_date": "2026-01-31", "profit_loss": -1199})).status_code == 422

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
        )
        assert expense.status_code == 201, expense.text
        expense_body = expense.json()
        assert expense_body["receipt_url"].startswith("/uploads/")
        assert (await client.patch(f"/api/expenses/{expense_body['id']}/reimbursed", json={"reimbursed": True})).status_code == 200

        settlements = await client.get("/api/salary/settlements", params={"period_start": "2026-01-01", "period_end": "2026-01-31"})
        assert settlements.status_code == 200, settlements.text
        settlement = settlements.json()["items"][0]
        assert settlement["payable_amount"] == "15.00"
        payment = await client.post(f"/api/salary/settlements/{settlement['id']}/pay", json={"amount": 10})
        assert payment.status_code == 201, payment.text
        assert payment.json()["settlement"]["unpaid_amount"] == "5.00"

        summary = (await client.get("/api/dashboard/summary")).json()
        assert summary["total_profit_loss"] == "-1200.00"
        assert summary["net_result"] == "-1335.00"

    print("api smoke: ok")


if __name__ == "__main__":
    asyncio.run(run())
