import os
import telebot
import yfinance as yf
import requests

# جلب التوكن من متغيرات البيئة
TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# إعداد جلسة الطلبات لتجاوز حظر Yahoo Finance
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "📈 *أهلاً بك في بوت أكاديمية سمو الأرقام (SMU)*\n\n"
        "أرسل رمز أي سهم لجلب التحليل المالي والأسعار المباشرة.\n"
        "• للأسهم السعودية: اكتب الرقم مباشرة (مثال: `2222` أو `7021`)\n"
        "• للأسهم الأمريكية: اكتب الرمز بالإنجليزية (مثال: `AAPL` أو `NVDA`)"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def get_stock_info(message):
    symbol_input = message.text.strip().upper()
    
    # تحويل الرمز المكتوب إلى صيغة Yahoo Finance
    if symbol_input.isdigit():
        ticker_symbol = f"{symbol_input}.SR"
    else:
        ticker_symbol = symbol_input

    try:
        # جلب البيانات عبر التيكر والجلسة المحدثة
        stock = yf.Ticker(ticker_symbol, session=session)
        info = stock.info
        
        # التأكد من وجود السعر
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        
        if not current_price:
            bot.reply_to(message, f"❌ تعذر جلب بيانات السهم `{symbol_input}`. تأكد من صحة الرمز.", parse_mode='Markdown')
            return

        company_name = info.get('longName') or info.get('shortName') or symbol_input
        currency = info.get('currency', 'SAR' if symbol_input.isdigit() else 'USD')
        pe_ratio = info.get('trailingPE', 'غير متوفر')
        market_cap = info.get('marketCap', 'غير متوفر')
        
        if isinstance(market_cap, (int, float)):
            market_cap = f"{market_cap / 1_000_000_000:.2f}B"

        response_text = (
            f"📊 *التحليل المالي - أكاديمية سمو الأرقام*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏢 *الشركة:* {company_name}\n"
            f"🏷️ *الرمز:* `{symbol_input}`\n"
            f"💰 *السعر اللحظي:* `{current_price}` {currency}\n"
            f"📈 *مكرر الربحية (P/E):* `{pe_ratio}`\n"
            f"🏛️ *القيمة السوقية:* `{market_cap}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ *أكاديمية سمو الأرقام لعلوم التداول*"
        )
        bot.reply_to(message, response_text, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ أثناء جلب البيانات: {str(e)}")

# تشغيل البوت
if __name__ == '__main__':
    bot.infinity_polling()
