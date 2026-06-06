"""成员垫付 Telegram 通知提交顺序测试。"""
import unittest
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from app.routers.expenses import _commit_expense_and_notify
from app.schemas.expense import MemberExpenseResponse
from app.services import telegram_service


def _expense_response() -> MemberExpenseResponse:
    """构造无需连接数据库的垫付响应对象。"""

    return MemberExpenseResponse(
        id=uuid.uuid4(),
        business_date=date(2026, 6, 6),
        member_id=uuid.uuid4(),
        member_name="加林",
        category_id=uuid.uuid4(),
        category_name="房租",
        amount=Decimal("200"),
        remark="法马古斯塔租金",
        receipt_url=None,
        reimbursed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class _FakeSession:
    """记录提交状态，模拟 SQLAlchemy session 的最小接口。"""

    def __init__(self, events: list[str], fail_commit: bool = False) -> None:
        self.events = events
        self.fail_commit = fail_commit
        self.committed = False
        self.rollback_called = False

    async def commit(self) -> None:
        self.events.append("commit")
        if self.fail_commit:
            raise RuntimeError("commit failed")
        self.committed = True

    async def rollback(self) -> None:
        self.rollback_called = True


class ExpenseNotificationOrderTests(unittest.IsolatedAsyncioTestCase):
    async def test_notification_runs_after_commit(self) -> None:
        events: list[str] = []
        session = _FakeSession(events)
        expense = _expense_response()
        operator = SimpleNamespace(id=uuid.uuid4(), name="加林")

        async def notify(expense_arg: MemberExpenseResponse, operator_name: str) -> None:
            self.assertIs(expense_arg, expense)
            self.assertEqual(operator_name, operator.name)
            self.assertTrue(session.committed)
            events.append("notify")

        with patch("app.routers.expenses.telegram_service.notify_member_expense", notify):
            await _commit_expense_and_notify(session, expense, operator)

        self.assertEqual(events, ["commit", "notify"])

    async def test_commit_failure_skips_notification(self) -> None:
        events: list[str] = []
        session = _FakeSession(events, fail_commit=True)
        expense = _expense_response()
        operator = SimpleNamespace(id=uuid.uuid4(), name="加林")

        async def notify(_: MemberExpenseResponse, operator_name: str) -> None:
            events.append(f"notify:{operator_name}")

        with patch("app.routers.expenses.telegram_service.notify_member_expense", notify):
            with self.assertRaises(RuntimeError):
                await _commit_expense_and_notify(session, expense, operator)

        self.assertEqual(events, ["commit"])

    async def test_notification_failure_keeps_committed_expense(self) -> None:
        events: list[str] = []
        session = _FakeSession(events)
        expense = _expense_response()
        operator = SimpleNamespace(id=uuid.uuid4(), name="加林")

        async def notify(_: MemberExpenseResponse, operator_name: str) -> None:
            events.append(f"notify:{operator_name}")
            raise RuntimeError("telegram failed")

        with patch("app.routers.expenses.telegram_service.notify_member_expense", notify):
            await _commit_expense_and_notify(session, expense, operator)

        self.assertTrue(session.committed)
        self.assertFalse(session.rollback_called)
        self.assertEqual(events, ["commit", f"notify:{operator.name}"])

    async def test_member_expense_notification_contains_expense_id(self) -> None:
        captured: list[str] = []
        expense = _expense_response()

        async def send(text: str) -> None:
            captured.append(text)

        with patch.object(telegram_service, "_send", send):
            await telegram_service.notify_member_expense(expense, operator_name="加林")

        self.assertEqual(len(captured), 1)
        self.assertIn(f"记录ID：</b> {expense.id}", captured[0])


if __name__ == "__main__":
    unittest.main()
