# ============================================================
# f2_config.py  —  সব settings এখানে
# ============================================================

# ── Telegram ──
BOT_TOKEN   = "8806117889:AAHfxPbHkDmImG7DFgWy0qXWXNS62U9-qiw"       # BotFather থেকে নিন
CHANNEL_ID  = "@RealTraderq"              # আপনার চ্যানেল

# ── Timezone ──
# Signal time UTC-06 (CST), display Bangladesh (UTC+06)
SIGNAL_TZ   = "America/Chicago"          # UTC-06
DISPLAY_TZ  = "Asia/Dhaka"               # UTC+06 Bangladesh

# ── Candle & Trading ──
CANDLE_MINS = 1                           # 1 মিনিট candle
ENTRY_OFFSET_MIN = 2                      # signal আসার পর entry time

# ── Free Data API (Twelve Data — free tier) ──
TWELVEDATA_API_KEY = "a4849499a77a4621bda2e0f4c2866a51"  # twelvedata.com/register

# ── Real Market Pairs (OTC নয়) ──
PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/GBP",
    "GBP/JPY",
    "EUR/JPY",
]

# ── Indicator Settings ──
RSI_PERIOD   = 14
MACD_FAST    = 12
MACD_SLOW    = 26
MACD_SIGNAL  = 9
BB_PERIOD    = 20
BB_STD       = 2.0

# ── Signal Filter ──
# তিনটি indicator একমত হলেই signal দেবে
MIN_CONFLUENCE = 3   # minimum কতটা indicator agree করতে হবে (max 4)

# ── Money Management ──
FIBONACCI_STEPS = [1, 1, 2, 3, 5, 8, 13]   # $1 balance-এর জন্য
MAX_LOSS_STREAK = 7                           # এর বেশি loss হলে STOP

# ── Schedule — প্রতি কত মিনিটে signal চেক করবে ──
CHECK_INTERVAL_MIN = 3    # প্রতি ৩ মিনিটে চেক
