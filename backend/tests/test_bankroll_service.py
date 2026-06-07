"""成员 bankroll 规则测试。"""
import unittest
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from app.routers.bankroll import _commit_bankroll_and_notify
from app.schemas.bankroll import BankrollEntryResponse
from app.services.bankroll_service import (
    calculate_balance_from_entries,
    calculate_signed_amount,
    validate_create_policy,
    validate_void_policy,
)


def _bankroll_response() -> BankrollEntryResponse:
    """构造无需连接数据库的 bankroll 响应对象。"""

    return BankrollEntryResponse(
        id=uuid.uuid4(),
        business_date=date(2026, 6, 6),
        member_id=uuid.uuid4(),
        member_name="加林",
        entry_type="top_up",
        amount=Decimal("500"),
        adjustment_direction=None,
        signed_amount=Decimal("500"),
        remark="补充现金",
        voided_at=None,
        void_reason=None,
        voided_by_member_id=None,
        voided_by_name=None,
        created_at=datetime.now(timezone.utc),
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


class BankrollServiceRuleTests(unittest.TestCase):
    def test_calculates_balance_from_effective_entries(self) -> None:
        balance = calculate_balance_from_entries([
            ("initial", Decimal("1000"), None),
            ("top_up", Decimal("500"), None),
            ("return", Decimal("200"), None),
            ("adjustment", Decimal("50"), "increase"),
            ("adjustment", Decimal("75"), "decrease"),
        ])

        self.assertEqual(balance, Decimal("1275"))

    def test_calculates_signed_amount_by_type(self) -> None:
        self.assertEqual(calculate_signed_amount("initial", Decimal("10")), Decimal("10"))
        self.assertEqual(calculate_signed_amount("top_up", Decimal("10")), Decimal("10"))
        self.assertEqual(calculate_signed_amount("return", Decimal("10")), Decimal("-10"))
        self.assertEqual(calculate_signed_amount("adjustment", Decimal("10"), "increase"), Decimal("10"))
        self.assertEqual(calculate_signed_amount("adjustment", Decimal("10"), "decrease"), Decimal("-10"))

    def test_rejects_duplicate_active_initial(self) -> None:
        with self.assertRaisesRegex(ValueError, "已经存在有效初始"):
            validate_create_policy(
                member_is_active=True,
                entry_type="initial",
                amount=Decimal("100"),
                adjustment_direction=None,
                remark=None,
                current_balance=Decimal("0"),
                has_active_initial=True,
            )

    def test_allows_initial_after_previous_initial_is_voided(self) -> None:
        validate_create_policy(
            member_is_active=True,
            entry_type="initial",
            amount=Decimal("100"),
            adjustment_direction=None,
            remark=None,
            current_balance=Decimal("0"),
            has_active_initial=False,
        )

    def test_rejects_return_over_current_balance(self) -> None:
        with self.assertRaisesRegex(ValueError, "退回金额不能超过"):
            validate_create_policy(
                member_is_active=True,
                entry_type="return",
                amount=Decimal("101"),
                adjustment_direction=None,
                remark=None,
                current_balance=Decimal("100"),
                has_active_initial=True,
            )

    def test_allows_decrease_adjustment_to_negative_balance(self) -> None:
        validate_create_policy(
            member_is_active=True,
            entry_type="adjustment",
            amount=Decimal("300"),
            adjustment_direction="decrease",
            remark="盘点差异",
            current_balance=Decimal("100"),
            has_active_initial=True,
        )
        balance = calculate_balance_from_entries([
            ("initial", Decimal("100"), None),
            ("adjustment", Decimal("300"), "decrease"),
        ])
        self.assertEqual(balance, Decimal("-200"))

    def test_inactive_member_cannot_initial_or_top_up_but_can_clear_balance(self) -> None:
        for entry_type in ("initial", "top_up"):
            with self.subTest(entry_type=entry_type):
                with self.assertRaisesRegex(ValueError, "停用成员不能"):
                    validate_create_policy(
                        member_is_active=False,
                        entry_type=entry_type,
                        amount=Decimal("100"),
                        adjustment_direction=None,
                        remark=None,
                        current_balance=Decimal("100"),
                        has_active_initial=False,
                    )

        validate_create_policy(
            member_is_active=False,
            entry_type="return",
            amount=Decimal("50"),
            adjustment_direction=None,
            remark=None,
            current_balance=Decimal("100"),
            has_active_initial=True,
        )
        validate_create_policy(
            member_is_active=False,
            entry_type="adjustment",
            amount=Decimal("50"),
            adjustment_direction="decrease",
            remark="清账",
            current_balance=Decimal("100"),
            has_active_initial=True,
        )

    def test_adjustment_requires_direction_and_reason(self) -> None:
        with self.assertRaisesRegex(ValueError, "选择增加或减少"):
            validate_create_policy(
                member_is_active=True,
                entry_type="adjustment",
                amount=Decimal("10"),
                adjustment_direction=None,
                remark="修正",
                current_balance=Decimal("0"),
                has_active_initial=False,
            )
        with self.assertRaisesRegex(ValueError, "必须填写原因"):
            validate_create_policy(
                member_is_active=True,
                entry_type="adjustment",
                amount=Decimal("10"),
                adjustment_direction="increase",
                remark=" ",
                current_balance=Decimal("0"),
                has_active_initial=False,
            )

    def test_void_requires_reason_and_rejects_duplicate_void(self) -> None:
        with self.assertRaisesRegex(ValueError, "作废原因不能为空"):
            validate_void_policy(is_voided=False, reason=" ")
        with self.assertRaisesRegex(ValueError, "已经作废"):
            validate_void_policy(is_voided=True, reason="金额登记错误")
        validate_void_policy(is_voided=False, reason="金额登记错误")


class BankrollNotificationOrderTests(unittest.IsolatedAsyncioTestCase):
    async def test_notification_runs_after_commit(self) -> None:
        events: list[str] = []
        session = _FakeSession(events)
        entry = _bankroll_response()
        operator = SimpleNamespace(id=uuid.uuid4(), name="加林")

        async def notify(entry_arg: BankrollEntryResponse, operator_name: str) -> None:
            self.assertIs(entry_arg, entry)
            self.assertEqual(operator_name, operator.name)
            self.assertTrue(session.committed)
            events.append("notify")

        with patch("app.routers.bankroll.telegram_service.notify_bankroll_entry", notify):
            await _commit_bankroll_and_notify(session, entry, operator)

        self.assertEqual(events, ["commit", "notify"])

    async def test_commit_failure_skips_notification(self) -> None:
        events: list[str] = []
        session = _FakeSession(events, fail_commit=True)
        entry = _bankroll_response()
        operator = SimpleNamespace(id=uuid.uuid4(), name="加林")

        async def notify(_: BankrollEntryResponse, operator_name: str) -> None:
            events.append(f"notify:{operator_name}")

        with patch("app.routers.bankroll.telegram_service.notify_bankroll_entry", notify):
            with self.assertRaises(RuntimeError):
                await _commit_bankroll_and_notify(session, entry, operator)

        self.assertEqual(events, ["commit"])

    async def test_notification_failure_keeps_committed_entry(self) -> None:
        events: list[str] = []
        session = _FakeSession(events)
        entry = _bankroll_response()
        operator = SimpleNamespace(id=uuid.uuid4(), name="加林")

        async def notify(_: BankrollEntryResponse, operator_name: str) -> None:
            events.append(f"notify:{operator_name}")
            raise RuntimeError("telegram failed")

        with patch("app.routers.bankroll.telegram_service.notify_bankroll_entry", notify):
            await _commit_bankroll_and_notify(session, entry, operator)

        self.assertTrue(session.committed)
        self.assertFalse(session.rollback_called)
        self.assertEqual(events, ["commit", f"notify:{operator.name}"])


if __name__ == "__main__":
    unittest.main()
