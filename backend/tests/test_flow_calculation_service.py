"""每日流水赢亏校验测试。"""
import unittest
from decimal import Decimal

from app.services.flow_calculation_service import calculate_profit_loss, validate_profit_loss


class FlowCalculationServiceTests(unittest.TestCase):
    def test_calculates_confirmed_example(self) -> None:
        result = calculate_profit_loss(
            principal=Decimal("1500"),
            chip_code=Decimal("0"),
            loss_rebate=Decimal("300"),
        )
        self.assertEqual(result, Decimal("-1200"))

    def test_accepts_matching_submitted_profit_loss(self) -> None:
        result = validate_profit_loss(
            principal=Decimal("1500"),
            chip_code=Decimal("0"),
            loss_rebate=Decimal("300"),
            submitted_profit_loss=Decimal("-1200"),
        )
        self.assertEqual(result, Decimal("-1200"))

    def test_rejects_mismatched_submitted_profit_loss(self) -> None:
        with self.assertRaisesRegex(ValueError, "赢亏校验失败"):
            validate_profit_loss(
                principal=Decimal("1500"),
                chip_code=Decimal("0"),
                loss_rebate=Decimal("300"),
                submitted_profit_loss=Decimal("-1199"),
            )


if __name__ == "__main__":
    unittest.main()
