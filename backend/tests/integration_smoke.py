"""本地 PostgreSQL 服务级冒烟验证。"""
import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.models.category import Category
from app.models.member import Member
from app.models.venue import Venue
from app.schemas.flow import DailyFlowCreate
from app.schemas.salary import SalaryPaymentCreate
from app.services import expense_service, flow_service, reporting_service, salary_service


async def run() -> None:
    """验证每日流水、垫付支出和工资月结的完整数据路径。"""

    async with AsyncSessionLocal() as session:
        await session.execute(text(
            "TRUNCATE salary_payments, salary_settlements, member_expenses, "
            "salary_accruals, daily_flow_reports, venues, categories, members CASCADE"
        ))
        member = Member(name="敏", role="成员")
        venue = Venue(name="Otium", rebate_rate=Decimal("0.2"))
        category = Category(name="餐饮费", type="expense")
        session.add_all([member, venue, category])
        await session.flush()

        flow = await flow_service.create_report(
            session,
            DailyFlowCreate(
                business_date=date(2026, 1, 30),
                member_id=member.id,
                venue_id=venue.id,
                game="俄罗斯",
                card_number="0",
                principal=Decimal("1500"),
                chip_code=Decimal("0"),
                loss_rebate=Decimal("300"),
                profit_loss=Decimal("-1200"),
            ),
        )
        assert flow.salary_amount == Decimal("15")

        try:
            await flow_service.create_report(
                session,
                DailyFlowCreate(
                    business_date=date(2026, 1, 30),
                    member_id=member.id,
                    venue_id=venue.id,
                    game="俄罗斯",
                    card_number="0",
                    principal=Decimal("1500"),
                    chip_code=Decimal("0"),
                    loss_rebate=Decimal("300"),
                    profit_loss=Decimal("-1200"),
                ),
            )
        except flow_service.DuplicateFlowError:
            pass
        else:
            raise AssertionError("重复流水必须被拒绝")
        await flow_service.delete_report(session, flow.id)
        flow = await flow_service.create_report(
            session,
            DailyFlowCreate(
                business_date=date(2026, 1, 30),
                member_id=member.id,
                venue_id=venue.id,
                game="俄罗斯",
                card_number="0",
                principal=Decimal("1500"),
                chip_code=Decimal("0"),
                loss_rebate=Decimal("300"),
                profit_loss=Decimal("-1200"),
            ),
        )
        assert flow.salary_amount == Decimal("15")

        try:
            await flow_service.create_report(
                session,
                DailyFlowCreate(
                    business_date=date(2026, 1, 31),
                    member_id=member.id,
                    venue_id=venue.id,
                    game="俄罗斯",
                    card_number="0",
                    principal=Decimal("1500"),
                    chip_code=Decimal("0"),
                    loss_rebate=Decimal("300"),
                    profit_loss=Decimal("-1199"),
                ),
            )
        except ValueError:
            pass
        else:
            raise AssertionError("赢亏不一致必须被拒绝")

        expense = await expense_service.create_expense(
            session,
            business_date=date(2026, 1, 30),
            member_id=member.id,
            amount=Decimal("120"),
            category_id=category.id,
            remark="团队晚餐",
            receipt_url=None,
        )
        assert expense.reimbursed is False
        expense = await expense_service.update_reimbursed(session, expense.id, True)
        assert expense.reimbursed is True

        settlements = await salary_service.list_settlements(
            session,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
        )
        assert settlements.total_payable == Decimal("15")
        payment = await salary_service.pay_settlement(
            session,
            settlements.items[0].id,
            SalaryPaymentCreate(amount=Decimal("10")),
        )
        assert payment.settlement.unpaid_amount == Decimal("5")

        summary = await reporting_service.get_summary(session)
        assert summary.total_profit_loss == Decimal("-1200")
        assert summary.total_expense == Decimal("120")
        assert summary.total_salary == Decimal("15")
        assert summary.net_result == Decimal("-1335")
        assert summary.unreimbursed_expense == Decimal("0")
        await session.commit()
    print("integration smoke: ok")


if __name__ == "__main__":
    asyncio.run(run())
