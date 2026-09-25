import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yfinance as yf

# جلب توكن البوت
TOKEN = os.environ.get('TOKEN') or os.environ.get('BOT_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 1. الترحيب عند بدء البوت
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك في بوت **أكاديمية سمو الأرقام (SMU)** 📊✨\n\n"
        "للحصول على تحليل مباشر لأي سهم، أرسل رمز السهم فقط:\n"
        "• الأسهم السعودية: أرسل الرقم فقط (مثال: `2222` لشركة أرامكو)\n"
        "• الأسهم الأمريكية: أرسل الرمز (مثال: `AAPL` أو `TSLA`)\n"
    )
    
    markup = InlineKeyboardMarkup()
    btn_saudi = InlineKeyboardButton(text="🇸🇦 قناة السوق السعودي", url="https://t.me/SumouAlArqam")
    btn_us = InlineKeyboardButton(text="🇺🇸 قناة السوق الأمريكي", url="https://t.me/SumouAlArqam")
    btn_website = InlineKeyboardButton(text="🌐 موقع أكاديمية سمو الأرقام", url="https://sumoualarqam.com")
    
    markup.add(btn_saudi)
    markup.add(btn_us)
    markup.add(btn_website)
    
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=markup)

# 2. تحليل السهم فور إرسال الرمز
@bot.message_handler(func=lambda message: True)
def analyze_stock(message):
    symbol = message.text.strip().upper()
    
    # تحويل رمز السوق السعودي لإمكانية قراءته
    if symbol.isdigit():
        ticker_symbol = f"{symbol}.SR"
    else:
        ticker_symbol = symbol

    bot.send_chat_action(message.chat.id, 'typing')

    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="5d")

        if hist.empty:
            bot.reply_to(message, f"❌ لم يتم العثور على بيانات للرمز: **{symbol}**. تأكد من صحة الرمز.", parse_mode='Markdown')
            return

        latest_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
        change = latest_price - prev_close
        change_pct = (change / prev_close) * 100
        
        high = hist['High'].max()
        low = hist['Low'].min()
        
        trend = "📈 صاعد" if change >= 0 else "📉 هابط"
        
        response_text = (
            f"📊 **تقرير تحليل أكاديمية سمو الأرقام (SMU)**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔹 **الرمز:** `{symbol}`\n"
            f"💵 **السعر الحالي:** {latest_price:.2f}\n"
            f"📈 **التغير:** {change:+.2f} ({change_pct:+.2f}%)\n"
            f"🧭 **الاتجاه القريب:** {trend}\n\n"
            f"🎯 **أعلى سعر (5 أيام):** {high:.2f}\n"
            f"🛡️ **أدنى سعر/دعم (5 أيام):** {low:.2f}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 *ملاحظة: هذا التحليل آلي بناءً على حركة السعر الأخيرة.*"
        )

        markup = InlineKeyboardMarkup()
        btn_channel = InlineKeyboardButton(text="📢 الانضمام لقناة التحليلات", url="https://t.me/SumouAlArqam")
        markup.add(btn_channel)

        bot.reply_to(message, response_text, parse_mode='Markdown', reply_markup=markup)

    except Exception as e:
        bot.reply_to(message, "⚠️ حدث خطأ أثناء جلب بيانات السهم، يرجى المحاولة لاحقاً.")

if __name__ == '__main__':
    bot.infinity_polling()
