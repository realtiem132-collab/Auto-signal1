# ============================================================
# f7_bot.py  —  Main Telegram Bot
# /start দিলে signal শুরু হয়, /stop দিলে বন্ধ
# ============================================================

import asyncio
import logging
import random
from datetime import datetime, timedelta

import pytz
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from f2_config import (
    BOT_TOKEN, CHANNEL_ID,
    CHECK_INTERVAL_MIN, DISPLAY_TZ,
    ENTRY_OFFSET_MIN,
)
from f5_signal_engine import generate_signal, scan_all_pairs, is_trading_allowed
from f6_message_builder import (
    build_signal_message,
    build_entry_alert,
    build_stop_message,
    build_welcome_message,
)

# ── Logging setup ──
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)

# ── Scheduler ──
scheduler = AsyncIOScheduler(timezone=pytz.timezone(DISPLAY_TZ))

# ── Bot instance (global) ──
_bot: Bot | None = None

# ── Active signal tracking ──
_pending_entry: dict | None = None


async def send_to_channel(text: str, parse_mode: str = "HTML") -> bool:
    """Channel-এ message পাঠায়।"""
    global _bot
    if _bot is None:
        logger.error("Bot not initialized")
        return False
    try:
        await _bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode=parse_mode,
        )
        return True
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False


async def signal_job():
    """
    Scheduler প্রতি CHECK_INTERVAL_MIN মিনিটে এটা call করে।
    সব pair scan → সেরা signal পাঠায়।
    """
    global _pending_entry

    if not is_trading_allowed():
        await send_to_channel(build_stop_message())
        scheduler.remove_job("signal_scan")
        logger.info("Trading stopped — max loss streak reached")
        return

    logger.info("Running signal scan...")
    sig = scan_all_pairs()

    if sig is None:
        logger.info("No valid signal found this cycle")
        return

    # Signal message পাঠাও
    msg = build_signal_message(sig)
    sent = await send_to_channel(msg)

    if sent:
        logger.info(
            f"Signal sent: {sig['pair']} {sig['direction']} "
            f"@ {sig['entry_time']} conf={sig['confidence']}%"
        )
        _pending_entry = sig

        # Entry time-এ alert schedule করো
        tz_bd = pytz.timezone(DISPLAY_TZ)
        now   = datetime.now(tz_bd)
        entry = now.replace(
            hour=sig["entry_h"],
            minute=sig["entry_m"],
            second=0,
            microsecond=0
        )
        if entry <= now:
            entry += timedelta(days=1)

        scheduler.add_job(
            entry_alert_job,
            trigger="date",
            run_date=entry,
            args=[sig],
            id=f"entry_{sig['entry_h']}_{sig['entry_m']}",
            replace_existing=True,
        )
        logger.info(f"Entry alert scheduled for {entry.strftime('%H:%M:%S')} BDT")


async def entry_alert_job(sig: dict):
    """
    Entry time হলে fire হয় — 'এন্ট্রি নিন' alert পাঠায়।
    """
    alert = build_entry_alert(sig)
    await send_to_channel(alert)
    logger.info(f"Entry alert sent for {sig['pair']} {sig['direction']}")


# ── /start command ─────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start দিলে:
    1. Welcome message পাঠায়
    2. ২ মিনিট পরে প্রথম signal
    3. তারপর প্রতি CHECK_INTERVAL_MIN মিনিটে
    """
    global _bot
    _bot = context.bot

    await update.message.reply_text(
        "✅ <b>Ai Signal Bot চালু হয়েছে!</b>\n\n"
        f"⏳ <b>{ENTRY_OFFSET_MIN} মিনিট পরে</b> প্রথম signal আসবে...\n"
        "📢 Signal channel-এ পাঠানো হবে।",
        parse_mode="HTML"
    )

    # Channel-এ welcome পাঠাও
    await send_to_channel(build_welcome_message())

    # পুরনো job থাকলে বন্ধ করো
    if scheduler.get_job("signal_scan"):
        scheduler.remove_job("signal_scan")

    # ২ মিনিট পরে প্রথম signal, তারপর interval
    tz_bd      = pytz.timezone(DISPLAY_TZ)
    first_run  = datetime.now(tz_bd) + timedelta(minutes=ENTRY_OFFSET_MIN)

    scheduler.add_job(
        signal_job,
        trigger="interval",
        minutes=CHECK_INTERVAL_MIN,
        next_run_time=first_run,
        id="signal_scan",
        replace_existing=True,
    )

    logger.info(
        f"/start received. First signal at {first_run.strftime('%H:%M:%S')} BDT, "
        f"then every {CHECK_INTERVAL_MIN} min"
    )


# ── /stop command ──────────────────────────────────────────
async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if scheduler.get_job("signal_scan"):
        scheduler.remove_job("signal_scan")
    await update.message.reply_text(
        "⛔ <b>Signal bot বন্ধ করা হয়েছে।</b>",
        parse_mode="HTML"
    )
    logger.info("/stop received — signal job removed")


# ── /status command ────────────────────────────────────────
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from f5_signal_engine import get_state, current_amount
    st  = get_state()
    amt = current_amount()
    job = scheduler.get_job("signal_scan")
    running = "✅ চলছে" if job else "⛔ বন্ধ"

    tz_bd = pytz.timezone(DISPLAY_TZ)
    now   = datetime.now(tz_bd).strftime("%H:%M:%S")

    text = (
        f"📊 <b>Bot Status</b>\n\n"
        f"🤖 Bot:        {running}\n"
        f"🕐 Time (BDT): <code>{now}</code>\n\n"
        f"🏆 Wins:       <b>{st['wins']}</b>\n"
        f"❌ Losses:     <b>{st['losses']}</b>\n"
        f"🔢 MM Step:    <b>{st['mm_step'] + 1}</b>\n"
        f"💵 Next Amt:   <b>${amt}</b>\n"
        f"📉 Loss Streak:<b>{st['loss_streak']}</b>\n"
    )
    await update.message.reply_text(text, parse_mode="HTML")


# ── MAIN ──────────────────────────────────────────────────
def main():
    global _bot

    logger.info("Starting Ai Signal Bot...")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    _bot = app.bot

    # Commands register
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("stop",   cmd_stop))
    app.add_handler(CommandHandler("status", cmd_status))

    # Scheduler start
    scheduler.start()
    logger.info("Scheduler started")

    # Bot run (blocking)
    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
