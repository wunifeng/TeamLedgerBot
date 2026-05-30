"""工资规则计算测试。"""
import unittest
from decimal import Decimal

from app.services.salary_rule_service import calculate_salary, list_games, list_rebate_rates


class SalaryRuleServiceTests(unittest.TestCase):
    def test_lists_fixed_games_and_supported_rates(self) -> None:
        self.assertEqual(list_rebate_rates(), [Decimal("0.1"), Decimal("0.2")])
        self.assertEqual(list_games(), ["BJ", "UTH", "俄罗斯", "百家乐"])

    def test_calculates_example_russian_salary_for_twenty_percent_rate(self) -> None:
        result = calculate_salary(Decimal("0.2"), "俄罗斯", Decimal("-1200"))
        self.assertEqual(result.salary_amount, Decimal("15"))
        self.assertEqual(result.rule_snapshot["rebate_rate"], "0.2")

    def test_uses_inclusive_boundary(self) -> None:
        result = calculate_salary(Decimal("0.2"), "BJ", Decimal("2600"))
        self.assertEqual(result.salary_amount, Decimal("50"))

    def test_returns_zero_when_no_interval_matches(self) -> None:
        result = calculate_salary(Decimal("0.2"), "百家乐", Decimal("100"))
        self.assertEqual(result.salary_amount, Decimal("0"))
        self.assertEqual(result.rule_description, "未命中工资区间")

    def test_rejects_unknown_game(self) -> None:
        with self.assertRaisesRegex(ValueError, "没有工资配置"):
            calculate_salary(Decimal("0.2"), "未知游戏", Decimal("1000"))


if __name__ == "__main__":
    unittest.main()
