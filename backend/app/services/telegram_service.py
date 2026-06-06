"""Telegram 群组通知服务。"""
import logging
from html import escape
from typing import Optional

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


async def notify_daily_flow(flow: DailyFlowResponse, operator_name: str) -> None:
    """发送新增每日流水通知。"""

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
        f"<b>备注：</b> {escape(flow.remark or '无')}\n"
        f"<b>操作人：</b> {escape(operator_name)}"
    )


async def notify_flow_updated(
    flow: DailyFlowResponse,
    operator_name: str,
    before_data: dict,
) -> None:
    """发送流水修改通知，包含关键字段变更前后对比。"""

    def fmt_diff(key: str, label: str) -> str:
        old = before_data.get(key)
        new_val = getattr(flow, key, None)
        if new_val is not None:
            new_val = str(new_val)
        if old != new_val:
            return f"<b>{label}：</b> {escape(str(old or '—'))} → {escape(str(new_val or '—'))}\n"
        return f"<b>{label}：</b> {escape(str(new_val or '—'))}\n"

    await _send(
        "<b>✏️ 修改每日流水</b>\n\n"
        f"<b>日期：</b> {flow.business_date}\n"
        f"<b>人员：</b> {escape(flow.member_name)}\n"
        f"<b>场子：</b> {escape(flow.venue_name)}\n"
        + fmt_diff("principal", "本金")
        + fmt_diff("chip_code", "点码")
        + fmt_diff("loss_rebate", "输反")
        + fmt_diff("profit_loss", "赢亏")
        + f"<b>工资：</b> {before_data.get('salary_amount', '—')} → {flow.salary_amount}\n"
        f"<b>操作人：</b> {escape(operator_name)}"
    )


async def notify_flow_deleted(snapshot: dict, operator_name: str) -> None:
    """发送流水删除通知。"""

    await _send(
        "<b>🗑️ 删除每日流水</b>\n\n"
        f"<b>日期：</b> {snapshot.get('business_date', '—')}\n"
        f"<b>人员：</b> {escape(snapshot.get('member_name', '—'))}\n"
        f"<b>场子：</b> {escape(snapshot.get('venue_name', '—'))}\n"
        f"<b>赢亏：</b> {snapshot.get('profit_loss', '—')}\n"
        f"<b>工资：</b> {snapshot.get('salary_amount', '—')}\n"
        f"<b>操作人：</b> {escape(operator_name)}"
    )


async def notify_member_expense(expense: MemberExpenseResponse, operator_name: str) -> None:
    """发送新增成员垫付支出通知。"""

    await _send(
        "<b>新增成员垫付支出</b>\n\n"
        f"<b>日期：</b> {expense.business_date}\n"
        f"<b>人员：</b> {escape(expense.member_name)}\n"
        f"<b>分类：</b> {escape(expense.category_name or '未分类')}\n"
        f"<b>金额：</b> {expense.amount}\n"
        f"<b>记录ID：</b> {expense.id}\n"
        f"<b>备注：</b> {escape(expense.remark or '无')}\n"
        f"<b>操作人：</b> {escape(operator_name)}"
    )


async def notify_expense_updated(
    expense: MemberExpenseResponse,
    operator_name: str,
    before_data: dict,
) -> None:
    """发送支出修改通知。"""

    old_amount = before_data.get("amount", "—")
    new_amount = str(expense.amount)

    await _send(
        "<b>✏️ 修改垫付支出</b>\n\n"
        f"<b>日期：</b> {expense.business_date}\n"
        f"<b>人员：</b> {escape(expense.member_name)}\n"
        f"<b>金额：</b> {escape(str(old_amount))} → {escape(new_amount)}\n"
        f"<b>分类：</b> {escape(expense.category_name or '未分类')}\n"
        f"<b>备注：</b> {escape(expense.remark or '无')}\n"
        f"<b>操作人：</b> {escape(operator_name)}"
    )


async def notify_expense_deleted(snapshot: dict, operator_name: str) -> None:
    """发送支出删除通知。"""

    await _send(
        "<b>🗑️ 删除垫付支出</b>\n\n"
        f"<b>人员：</b> {escape(snapshot.get('member_name', '—'))}\n"
        f"<b>金额：</b> {snapshot.get('amount', '—')}\n"
        f"<b>分类：</b> {escape(snapshot.get('category_name') or '未分类')}\n"
        f"<b>备注：</b> {escape(snapshot.get('remark') or '无')}\n"
        f"<b>操作人：</b> {escape(operator_name)}"
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


async def notify_salary_payment_voided(result: SalaryPaymentResponse, operator_name: str) -> None:
    """发送工资发放作废通知。"""

    await _send(
        "<b>工资发放作废</b>\n\n"
        f"<b>人员：</b> {escape(result.settlement.member_name)}\n"
        f"<b>账期：</b> {result.settlement.period_start} 至 {result.settlement.period_end}\n"
        f"<b>作废金额：</b> {result.payment.amount}\n"
        f"<b>剩余未付：</b> {result.settlement.unpaid_amount}\n"
        f"<b>作废原因：</b> {escape(result.payment.void_reason or '无')}\n"
        f"<b>操作人：</b> {escape(operator_name)}"
    )
