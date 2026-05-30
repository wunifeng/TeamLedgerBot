"""工资规则加载与计算。"""
import json
import os
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

_ZERO = Decimal("0")


def _decimal_key(value: Decimal) -> str:
    return format(value.normalize(), "f")


@dataclass(frozen=True)
class SalaryCalculation:
    """单条流水对应的工资计算结果。"""

    salary_amount: Decimal
    rule_description: str
    rule_snapshot: dict[str, Any]


@lru_cache(maxsize=1)
def load_salary_config() -> dict[str, dict[str, list[dict[str, Any]]]]:
    """从版本化 JSON 文件加载工资配置。"""

    default_path = Path(__file__).resolve().parent.parent / "data" / "salary_config.json"
    path = Path(os.getenv("SALARY_CONFIG_PATH", str(default_path)))
    with path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def reload_salary_config() -> None:
    """清理缓存，供测试和配置更新后显式刷新。"""

    load_salary_config.cache_clear()


def list_rebate_rates() -> list[Decimal]:
    """返回配置支持的输返比例。"""

    return sorted(Decimal(key) for key in load_salary_config())


def list_games() -> list[str]:
    """返回工资配置中出现的固定游戏。"""

    games = {
        game
        for games_by_rate in load_salary_config().values()
        for game in games_by_rate
    }
    return sorted(games)


def supports_rebate_rate(rebate_rate: Decimal) -> bool:
    """判断场子输返比例是否存在工资规则。"""

    return _decimal_key(rebate_rate) in load_salary_config()


def calculate_salary(
    rebate_rate: Decimal,
    game: str,
    profit_loss: Decimal,
) -> SalaryCalculation:
    """按场子输返比例、游戏和赢亏区间计算工资。"""

    rate_key = _decimal_key(rebate_rate)
    games_by_rate = load_salary_config().get(rate_key)
    if games_by_rate is None:
        raise ValueError(f"输返比例 {rate_key} 没有工资配置。")

    rules = games_by_rate.get(game)
    if rules is None:
        raise ValueError(f"游戏 {game} 没有工资配置。")

    for rule in rules:
        if not rule.get("enabled", False):
            continue
        profit_min = Decimal(str(rule["profit_min"])) if rule["profit_min"] is not None else None
        profit_max = Decimal(str(rule["profit_max"])) if rule["profit_max"] is not None else None
        if profit_min is not None and profit_loss < profit_min:
            continue
        if profit_max is not None and profit_loss > profit_max:
            continue

        salary = Decimal(str(rule["salary"]))
        return SalaryCalculation(
            salary_amount=salary,
            rule_description=str(rule["description"]),
            rule_snapshot={
                "rebate_rate": rate_key,
                "game": game,
                "profit_loss": str(profit_loss),
                "profit_min": str(profit_min) if profit_min is not None else None,
                "profit_max": str(profit_max) if profit_max is not None else None,
                "salary": str(salary),
                "description": str(rule["description"]),
            },
        )

    return SalaryCalculation(
        salary_amount=_ZERO,
        rule_description="未命中工资区间",
        rule_snapshot={
            "rebate_rate": rate_key,
            "game": game,
            "profit_loss": str(profit_loss),
            "salary": "0",
            "description": "未命中工资区间",
        },
    )
