// f3_bot.js
const TelegramBot = require('node-telegram-bot-api');
const moment = require('moment-timezone');
const config = require('./f1_config');
const { analyzeMarket } = require('./f2_analyzer');

// বট ইনিশিয়ালাইজেশন
const bot = new TelegramBot(config.TELEGRAM_TOKEN, { polling: true });

console.log("Telegram Bot is running...");

// /start কমান্ড হ্যান্ডলার
bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(chatId, "📊 Quotex Real Market Signal Bot Started!\nপ্রতি ১ মিনিট পর পর রিয়াল মার্কেটের সিগন্যাল পাঠানো হবে।");

    // প্রতি ৬০ সেকেন্ড (১ মিনিট) পর পর সিগন্যাল চেক করার টাইমার
    setInterval(() => {
        config.PAIRS.forEach((pair) => {
            const analysis = analyzeMarket(pair);
            
            // শুধুমাত্র স্ট্রং CALL বা PUT সিগন্যাল হলে মেসেজ পাঠাবে
            if (analysis.action !== 'NEUTRAL') {
                
                // বাংলাদেশ সময় ফরমেট (UTC+6)
                const bdTime = moment().tz(config.TIMEZONE).format('hh:mm:ss A');
                
                const message = `
🎯 **NEW SIGNAL** 🎯
━━━━━━━━━━━━━━━━━━
💱 **Asset:** ${analysis.pair} (Real Market)
⏰ **Time (BD):** ${bdTime}
⏳ **Duration:** 1 MINUTE
📈 **Direction:** ${analysis.action}
📊 **RSI Level:** ${analysis.rsi}
━━━━━━━━━━━━━━━━━━
⚠️ *নিজ দায়িত্বে ট্রেড করুন। ওটিসি মার্কেটে এটি কাজ করবে না।*
                `;
                
                bot.sendMessage(chatId, message, { parse_mode: 'Markdown' });
            }
        });
    }, 60000); // 60000 ms = 1 Minute
});