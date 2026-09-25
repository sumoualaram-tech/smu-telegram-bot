import os
import telebot
import yfinance as yf

# جلب التوكن من متغيرات البيئة
TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

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
    
    # تحويل الرمز المكتوب إلى صيغة Yahoo Finance للأسهم السعودية والأمريكية
    if symbol_input.isdigit():
        ticker_symbol = f"{symbol_input}.SR"
    else:
        ticker_symbol = symbol_input

    try:
        stock = yf.Ticker(ticker_symbol)
        
        # جلب أحدث بيانات السعر مباشرة عبر التاريخ اللحظي تفادياً لحظر Yahoo 401
        hist = stock.history(period="5d")
        
        if hist.empty:
            bot.reply_to(message, f"❌ تعذر جلب بيانات السهم `{symbol_input}`. تأكد من صحة الرمز.", parse_mode='Markdown')
            return

        current_price = round(hist['Close'].iloc[-1], 2)
        prev_close = round(hist['Close'].iloc[-2], 2) if len(hist) > 1 else current_price
        change = round(current_price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)
        
        status_icon = "🟢" if change >= 0 else "🔴"
        currency = "SAR" if symbol_input.isdigit() else "USD"

        response_text = (
            f"📊 *التحليل السعري والمالي - أكاديمية سمو الأرقام*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ *الرمز:* `{symbol_input}`\n"
            f"💰 *السعر اللحظي:* `{current_price}` {currency}\n"
            f"{status_icon} *التغير اليومي:* `{change:+}` ({change_pct:+}%)\n"
            f"📉 *الإغلاق السابق:* `{prev_close}` {currency}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ *أكاديمية سمو الأرقام لعلوم التداول*"
        )
        bot.reply_to(message, response_text, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ أثناء جلب البيانات، يرجى المحاولة لاحقاً.")

if __name__ == '__main__':
    bot.infinity_polling()
