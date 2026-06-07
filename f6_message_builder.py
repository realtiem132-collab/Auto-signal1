# ============================================================
# f6_message_builder.py  —  Telegram message format করে
# ============================================================

from datetime import datetime
import pytz
from f2_config import DISPLAY_TZ, FIBONACCI_STEPS, MAX_LOSS_STREAK


def _bd_time() -> str:
    tz = pytz.timezone(DISPLAY_TZ)
    return datetime.now(tz).strftime("%H:%M:%S")


def _vote_emoji(vote: str, direction: str) -> str:
    if vote == direction:
        return "✅"
    elif vote == "NEUTRAL":
        return "⚪"
    else:
        return "❌"


def build_signal_message(sig: dict) -> str:
    """
    Signal dict থেকে Telegram message তৈরি করে।
    HTML parse_mode ব্যবহার করে।
    """
    is_call = sig["direction"] == "CALL"
    dir_emoji = "🟢" if is_call else "🔴"
    dir_word  = "⬆️ CALL / UP" if is_call else "⬇️ PUT / DOWN"
    arrow     = "📈" if is_call else "📉"

    votes = sig.get("votes", {})
    v_rsi  = _vote_emoji(votes.get("RSI",  "NEUTRAL"), sig["direction"])
    v_macd = _vote_emoji(votes.get("MACD", "NEUTRAL"), sig["direction"])
    v_bb   = _vote_emoji(votes.get("BB",   "NEUTRAL"), sig["direction"])
    v_mtf  = _vote_emoji(votes.get("MTF",  "NEUTRAL"), sig["direction"])

    mtf_status = "✅ 1m + 5m Aligned" if sig.get("mtf_agree") else "⚠️ Mixed TF"
    conf_bar   = _progress_bar(sig["confidence"], 100, length=10)
    mm_bar     = _mm_table(sig["mm_step"] - 1)

    msg = (
        f"{'✦' * 14}\n"
        f"⚡ <b>Ai SIGNAL BOT</b> ⚡\n"
        f"{'✦' * 14}\n\n"

        f"{arrow} <b>REAL MARKET SIGNAL</b> {arrow}\n"
        f"📡 <b>1 Minute Candle</b>\n\n"

        f"┌─────────────────────┐\n"
        f"│ 📊 <b>Market</b>  »  <code>{sig['pair']}</code>\n"
        f"│ ⏰ <b>Entry</b>   »  <code>{sig['entry_time']}</code>  🇧🇩 BDT\n"
        f"│ {dir_emoji} <b>Direction</b> »  <b>{dir_word}</b>\n"
        f"│ 💵 <b>Amount</b>  »  <b>${sig['amount']}</b>\n"
        f"│ 📡 <b>Price</b>   »  <code>{sig['price_str']}</code>\n"
        f"└─────────────────────┘\n\n"

        f"📊 <b>Indicator Analysis</b>\n"
        f"├ {v_rsi}  RSI-14        :  <code>{sig['rsi']:.1f}</code>"
        f"{'  🔴 OB' if sig['rsi'] > 70 else ('  🟢 OS' if sig['rsi'] < 30 else '')}\n"
        f"├ {v_macd} MACD Hist     :  <code>{'▲ +' if sig['macd_hist'] > 0 else '▼ '}{abs(sig['macd_hist']):.6f}</code>\n"
        f"├ {v_bb}  Bollinger %B  :  <code>{sig['bb_pct_b']:.2f}</code>"
        f"{'  (Above Mid)' if sig['bb_pct_b'] > 0.5 else '  (Below Mid)'}\n"
        f"└ {v_mtf} MTF (1m+5m)   :  {mtf_status}\n\n"

        f"🎯 <b>Confidence</b>: {conf_bar} <b>{sig['confidence']}%</b>\n\n"

        f"{mm_bar}\n"

        f"🏆 WIN: <b>{sig['wins']}</b>  |  ❌ LOSS: <b>{sig['losses']}</b>\n\n"

        f"⏱ <i>Signal generated: {_bd_time()} BDT</i>\n"
        f"✦ ▪ ══ ‼ Ai Tools SIGNAL ‼ ══ ▪ ✦\n"
        f"📢 t.me/RealTraderq"
    )
    return msg


def build_entry_alert(sig: dict) -> str:
    """
    Entry time হলে যে alert পাঠায়।
    """
    is_call   = sig["direction"] == "CALL"
    dir_emoji = "🟢" if is_call else "🔴"
    dir_word  = "⬆️ UP / CALL" if is_call else "⬇️ DOWN / PUT"
    fire      = "🔥" * 5

    return (
        f"{fire}\n"
        f"⚡ <b>এন্ট্রি নিন এখনই!</b> ⚡\n"
        f"{fire}\n\n"
        f"📊 <b>{sig['pair']}</b>\n"
        f"{dir_emoji} <b>{dir_word}</b>\n"
        f"💵 Amount: <b>${sig['amount']}</b>\n"
        f"⏰ Entry: <code>{sig['entry_time']}</code> BDT\n\n"
        f"✦ ▪ ══ ‼ Ai SIGNAL BOT ‼ ══ ▪ ✦"
    )


def build_stop_message() -> str:
    return (
        "⛔ <b>সব স্টেপ শেষ!</b>\n\n"
        f"আজকের জন্য ট্রেড বন্ধ রাখুন।\n"
        f"সর্বোচ্চ {MAX_LOSS_STREAK}টি loss হয়েছে।\n\n"
        "💡 পরের সেশনে আবার শুরু করুন।"
    )


def build_welcome_message() -> str:
    steps_text = "\n".join(
        f"  Step {i+1}: ${amt}"
        for i, amt in enumerate(FIBONACCI_STEPS)
    )
    return (
        "👋 <b>Ai Signal Bot চালু হয়েছে!</b>\n\n"
        "📡 <b>Real Market Signal</b>\n"
        "⏱ 1 Minute Candle\n"
        "🇧🇩 Bangladesh Time (UTC+06)\n\n"
        "💰 <b>Money Management (Fibonacci):</b>\n"
        f"<code>{steps_text}</code>\n\n"
        "⚠️ <b>সতর্কতা:</b> ট্রেডিং-এ risk আছে।\n"
        "নিজের দায়িত্বে ট্রেড করুন।\n\n"
        "✦ ▪ ══ ‼ Ai Tools SIGNAL ‼ ══ ▪ ✦\n"
        "📢 t.me/RealTraderq"
    )


def _progress_bar(value: int, total: int, length: int = 10) -> str:
    filled = round((value / total) * length)
    return "█" * filled + "░" * (length - filled)


def _mm_table(current_step: int) -> str:
    lines = ["💰 <b>Money Management</b>"]
    for i, amt in enumerate(FIBONACCI_STEPS):
        if i < current_step:
            lines.append(f"  ~~Step {i+1}: ${amt}~~  ✗")
        elif i == current_step:
            lines.append(f"  ▶️ <b>Step {i+1}: ${amt}  ← এখন</b>")
        else:
            lines.append(f"  Step {i+1}: ${amt}")
    return "\n".join(lines)
