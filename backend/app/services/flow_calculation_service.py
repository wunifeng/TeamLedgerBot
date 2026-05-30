"""每日流水校验所需的纯计算函数。"""
from decimal import Decimal


def calculate_profit_loss(
    principal: Decimal,
    chip_code: Decimal,
    loss_rebate: Decimal,
) -> Decimal:
    """根据本金、点码和输反计算最终赢亏。"""

    return chip_code + loss_rebate - principal


def validate_profit_loss(
    principal: Decimal,
    chip_code: Decimal,
    loss_rebate: Decimal,
    submitted_profit_loss: Decimal,
) -> Decimal:
    """校验成员填写的赢亏，返回系统计算结果。"""

    calculated = calculate_profit_loss(principal, chip_code, loss_rebate)
    if calculated != submitted_profit_loss:
        raise ValueError(
            "赢亏校验失败："
            f"点码 {chip_code} + 输反 {loss_rebate} - 本金 {principal} = {calculated}，"
            f"与填写值 {submitted_profit_loss} 不一致。"
        )
    return calculated
