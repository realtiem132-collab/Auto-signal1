# 📋 Setup Guide — Ai Signal Bot

## ফাইল গুলোর কাজ

| ফাইল | কাজ |
|------|-----|
| `f1_requirements.txt` | সব Python library |
| `f2_config.py` | BOT TOKEN, API KEY, সব settings |
| `f3_data_fetcher.py` | Twelve Data API থেকে candle data |
| `f4_indicators.py` | RSI, MACD, Bollinger, MTF calculation |
| `f5_signal_engine.py` | Signal generate + filter logic |
| `f6_message_builder.py` | Telegram message format |
| `f7_bot.py` | Main bot — /start /stop /status |
| `f8_setup_guide.md` | এই guide |

---

## Step 1 — Bot Token নিন
1. Telegram-এ `@BotFather` তে যান
2. `/newbot` লিখুন
3. নাম দিন → Token কপি করুন
4. `f2_config.py` তে `BOT_TOKEN = "..."` এ paste করুন

## Step 2 — Twelve Data API Key নিন (Free)
1. https://twelvedata.com/register তে account করুন
2. Dashboard থেকে API Key কপি করুন
3. `f2_config.py` তে `TWELVEDATA_API_KEY = "..."` এ paste করুন
4. Free plan: **800 requests/day** — যথেষ্ট

## Step 3 — Channel Setup
1. Bot-কে আপনার channel-এর Admin করুন
2. `f2_config.py` তে `CHANNEL_ID = "@RealTraderq"` ঠিক আছে কিনা দেখুন

## Step 4 — Install করুন
```bash
pip install -r f1_requirements.txt
```

## Step 5 — চালু করুন
```bash
python f7_bot.py
```

## Step 6 — Bot-এ কমান্ড দিন
- `/start` → bot চালু, ২ মিনিট পরে প্রথম signal
- `/stop`  → signal বন্ধ
- `/status` → কতটা win/loss, কোন step আছে

---

## Signal Logic
- **Data**: Real market (EUR/USD, GBP/USD etc.) — Twelve Data API
- **Candle**: 1 minute
- **Time**: Bangladesh time (UTC+06) তে entry time দেখাবে
- **Entry**: Signal আসার ঠিক 2 মিনিট পরে entry
- **Indicators**: RSI-14 + MACD + Bollinger Band + MTF (1m+5m)
- **Filter**: কমপক্ষে ৩টি indicator agree করলে signal যাবে
- **MM**: Fibonacci $1→$1→$2→$3→$5→$8→$13

---

## সমস্যা হলে

| সমস্যা | সমাধান |
|--------|---------|
| Bot respond করছে না | BOT_TOKEN সঠিক কিনা দেখুন |
| Signal আসছে না | TWELVEDATA_API_KEY দিয়েছেন কিনা দেখুন |
| Channel-এ যাচ্ছে না | Bot-কে channel admin করেছেন কিনা দেখুন |
| `ModuleNotFoundError` | `pip install -r f1_requirements.txt` আবার দিন |
| API error | Free plan-এ দিনে ৮০০ request — বেশি হলে পরদিন |

---

## log দেখতে
```bash
tail -f bot.log
```
