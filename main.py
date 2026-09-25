import os
import telebot
from telebot import types
import yfinance as yf
import mplfinance as mpf
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import io

# جلب التوكن من متغيرات البيئة
TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# خادم المنفذ للحفاظ على إبقاء Render شغالاً
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SMU Bot is Running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# قائمة الأزرار الرئيسية
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📊 تحليل سهم (سعودي/أمريكي)")
    btn2 = types.KeyboardButton("📈 الشارت الفني المباشر")
    btn3 = types.KeyboardButton("🎓 عن أكاديمية سمو الأرقام")
    btn4 = types.KeyboardButton("❓ طريقة الاستخدام")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "📈 *أهلاً بك في بوت أكاديمية سمو الأرقام (SMU)*\n\n"
        "اختر من الأقسام أدناه أو أرسل رمز أي سهم مباشرة (مثل `2222` أو `AAPL`)."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text in ["📊 تحليل سهم (سعودي/أمريكي)", "📈 الشارت الفني المباشر"])
def prompt_for_symbol(message):
    bot.reply_to(message, "💬 اكتب رمز السهم المطلوب (مثال: `2222` للسعودي أو `NVDA` للأمريكي):", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🎓 عن أكاديمية سمو الأرقام")
def about_smu(message):
    info = (
        "🏛️ *أكاديمية سمو الأرقام (SMU)*\n\n"
        "متخصصون في علوم التداول، التحليل الرقمي، والدورات الزمنية للأسواق المالية.\n"
        "نقدم أدوات تحليلية متقدمة لمساعدة المتداول في اتخاذ القرار الصائب."
    )
    bot.send_message(message.chat.id, info, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "❓ طريقة الاستخدام")
def usage_help(message):
    help_msg = (
        "📖 *طريقة الاستخدام:*\n\n"
        "• *للأسهم السعودية:* أرسل رقم السهم فقط (مثال: `2222` لـ أرامكو، `7021` لـ أنابيب).\n"
        "• *للأسهم الأمريكية:* أرسل الرمز بالإنجليزية (مثال: `AAPL` لـ أبل، `NVDA` لـ إنفيديا)."
    )
    bot.send_message(message.chat.id, help_msg, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def process_stock(message):
    symbol_input = message.text.strip().upper()
    if symbol_input.startswith('/'):
        return

    ticker_symbol = f"{symbol_input}.SR" if symbol_input.isdigit() else symbol_input

    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="60d")

        if hist.empty:
            bot.reply_to(message, f"❌ تعذر جلب بيانات السهم `{symbol_input}`. تأكد من صحة الرمز.", parse_mode='Markdown')
            return

        current_price = round(hist['Close'].iloc[-1], 2)
        prev_close = round(hist['Close'].iloc[-2], 2) if len(hist) > 1 else current_price
        change = round(current_price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)
        high_price = round(hist['High'].iloc[-1], 2)
        low_price = round(hist['Low'].iloc[-1], 2)
        
        status_icon = "🟢" if change >= 0 else "🔴"
        currency = "SAR" if symbol_input.isdigit() else "USD"

        # توليد الشارت الفني كصورة
        buf = io.BytesIO()
        mpf.plot(hist.tail(30), type='candle', style='charles', title=f"{symbol_input} Chart", savefig=buf)
        buf.seek(0)

        response_text = (
            f"📊 *التحليل الشامل - أكاديمية سمو الأرقام*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ *الرمز:* `{symbol_input}`\n"
            f"💰 *السعر اللحظي:* `{current_price}` {currency}\n"
            f"{status_icon} *التغير اليومي:* `{change:+}` ({change_pct:+}%)\n"
            f"📈 *أعلى سعر اليوم:* `{high_price}` {currency}\n"
            f"📉 *أدنى سعر اليوم:* `{low_price}` {currency}\n"
            f"🔻 *الإغلاق السابق:* `{prev_close}` {currency}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ *أكاديمية سمو الأرقام لعلوم التداول*"
        )

        bot.send_photo(message.chat.id, photo=buf, caption=response_text, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ أثناء معالجة البيانات، يرجى المحاولة لاحقاً.")

if __name__ == '__main__':
    bot.infinity_polling()
