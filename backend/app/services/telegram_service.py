"""Telegram 群组通知服务。"""
import logging
from html import escape

import httpx

from app.config import settings
from app.schemas.expense import MemberExpenseResponse
from app.schemas.flow import DailyFlowResponse
from app.schemas.salary import SalaryPaymentResponse

logger = logging.getLogger(__name__)
_API = "https://api.telegram.org/bot{token}/sendMessage"


async def _send(text: str) -> None:
    """向群组发送通知。通知失败不影响业务数据写入。"""

    url = _API.format(token=settings.TELEGRAM_BOT_TOKEN)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            )
            if not response.is_success:
                logger.warning("Telegram API %s: %s", response.status_code, response.text[:200])
    except Exception as exc:
        logger.error("Telegram send failed: %s", exc)


async def notify_daily_flow(flow: DailyFlowResponse) -> None:
    """发送每日流水通知。"""

    await _send(
        "<b>新增每日流水</b>\n\n"
        f"<b>日期：</b> {flow.business_date}\n"
        f"<b>人员：</b> {escape(flow.member_name)}\n"
        f"<b>场子：</b> {escape(flow.venue_name)}\n"
        f"<b>游戏：</b> {escape(flow.game)}\n"
        f"<b>卡号：</b> {escape(flow.card_number)}\n"
        f"<b>本金：</b> {flow.principal}\n"
        f"<b>点码：</b> {flow.chip_code}\n"
        f"<b>输反：</b> {flow.loss_rebate}\n"
        f"<b>赢亏：</b> {flow.profit_loss}\n"
        f"<b>工资：</b> {flow.salary_amount}\n"
        f"<b>备注：</b> {escape(flow.remark or '无')}"
    )


async def notify_member_expense(expense: MemberExpenseResponse) -> None:
    """发送成员垫付支出通知。"""

    await _send(
        "<b>新增成员垫付支出</b>\n\n"
        f"<b>日期：</b> {expense.business_date}\n"
        f"<b>人员：</b> {escape(expense.member_name)}\n"
        f"<b>分类：</b> {escape(expense.category_name or '未分类')}\n"
        f"<b>金额：</b> {expense.amount}\n"
        f"<b>备注：</b> {escape(expense.remark or '无')}"
    )


async def notify_salary_payment(result: SalaryPaymentResponse) -> None:
    """发送工资实际发放通知。"""

    await _send(
        "<b>工资发放</b>\n\n"
        f"<b>人员：</b> {escape(result.settlement.member_name)}\n"
        f"<b>账期：</b> {result.settlement.period_start} 至 {result.settlement.period_end}\n"
        f"<b>本次发放：</b> {result.payment.amount}\n"
        f"<b>剩余未付：</b> {result.settlement.unpaid_amount}\n"
        f"<b>备注：</b> {escape(result.payment.remark or '无')}"
    )
