"""Telegram Bot notification service — formats and sends HTML messages."""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

import httpx
import pytz

from app.config import settings

logger = logging.getLogger(__name__)
_API = "https://api.telegram.org/bot{token}/sendMessage"


def _fmt_time(dt: datetime) -> str:
    tz = pytz.timezone(settings.TIMEZONE)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M")


async def _send(text: str) -> None:
    """Post HTML message to configured Telegram chat (never raises)."""
    url = _API.format(token=settings.TELEGRAM_BOT_TOKEN)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                url,
                json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            )
            if not r.is_success:
                logger.warning("Telegram API %s: %s", r.status_code, r.text[:200])
    except Exception as exc:
        logger.error("Telegram send failed: %s", exc)


async def notify_income(
    member_name: str, amount: Decimal, category_name: Optional[str],
    remark: Optional[str], created_at: datetime,
) -> None:
    await _send(
        f"📥 <b>新增收入</b>\n\n"
        f"👤 <b>成员：</b> {member_name}\n"
        f"💰 <b>金额：</b> ${amount:,.2f}\n"
        f"📦 <b>分类：</b> {category_name or '—'}\n"
        f"📝 <b>备注：</b> {remark or '—'}\n\n"
        f"⏰ <b>时间：</b> {_fmt_time(created_at)}"
    )


async def notify_expense(
    member_name: str, amount: Decimal, category_name: Optional[str],
    remark: Optional[str], created_at: datetime,
) -> None:
    await _send(
        f"💸 <b>新增支出</b>\n\n"
        f"👤 <b>成员：</b> {member_name}\n"
        f"💰 <b>金额：</b> ${amount:,.2f}\n"
        f"📦 <b>分类：</b> {category_name or '—'}\n"
        f"📝 <b>备注：</b> {remark or '—'}\n\n"
        f"⏰ <b>时间：</b> {_fmt_time(created_at)}"
    )


async def notify_salary(
    member_name: str, salary_amount: Decimal, bonus: Optional[Decimal],
    remark: Optional[str], created_at: datetime,
) -> None:
    bonus_line = f"🎁 <b>奖金：</b> ${bonus:,.2f}\n" if bonus else ""
    await _send(
        f"💼 <b>新增薪资</b>\n\n"
        f"👤 <b>成员：</b> {member_name}\n"
        f"💰 <b>基础薪资：</b> ${salary_amount:,.2f}\n"
        f"{bonus_line}"
        f"📝 <b>备注：</b> {remark or '—'}\n\n"
        f"⏰ <b>时间：</b> {_fmt_time(created_at)}"
    )


async def alert_high_amount(
    member_name: str, amount: Decimal, tx_type: str, created_at: datetime,
) -> None:
    threshold = settings.RISK_HIGH_AMOUNT_THRESHOLD
    await _send(
        f"⚠️ <b>[风险告警] 异常高额</b>\n\n"
        f"👤 <b>成员：</b> {member_name}\n"
        f"💰 <b>金额：</b> ${amount:,.2f}\n"
        f"📊 <b>类型：</b> {tx_type}\n"
        f"🔴 <b>阈值：</b> ${threshold:,.0f}\n\n"
        f"⏰ <b>时间：</b> {_fmt_time(created_at)}\n请及时核查！"
    )


async def alert_duplicate(
    member_name: str, amount: Decimal, tx_type: str, created_at: datetime,
) -> None:
    win = settings.RISK_DUPLICATE_WINDOW_SECONDS // 60
    await _send(
        f"⚠️ <b>[风险告警] 疑似重复提交</b>\n\n"
        f"👤 <b>成员：</b> {member_name}\n"
        f"💰 <b>金额：</b> ${amount:,.2f}\n"
        f"📊 <b>类型：</b> {tx_type}\n"
        f"🟡 <b>规则：</b> {win} 分钟内相同记录\n\n"
        f"⏰ <b>时间：</b> {_fmt_time(created_at)}\n请及时核查！"
    )


async def alert_high_frequency(
    member_name: str, tx_type: str, created_at: datetime,
) -> None:
    limit = settings.RISK_FREQUENCY_LIMIT
    win = settings.RISK_FREQUENCY_WINDOW_SECONDS // 60
    await _send(
        f"⚠️ <b>[风险告警] 提交频率异常</b>\n\n"
        f"👤 <b>成员：</b> {member_name}\n"
        f"📊 <b>类型：</b> {tx_type}\n"
        f"🟡 <b>规则：</b> {win} 分钟内超过 {limit} 笔\n\n"
        f"⏰ <b>时间：</b> {_fmt_time(created_at)}\n请及时核查！"
    )
