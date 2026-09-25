import os
import telebot
from telebot import types
import yfinance as yf
import mplfinance as mpf
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import io
import math

# جلب التوكن من متغيرات البيئة
TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# خادم المنفذ للحفاظ على استقرار Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"SMU Universal Bot Active!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# قائمة الأزرار التفاعلية
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("🌐 التحليل الموحد (كل مدارس التحليل)")
    btn2 = types.KeyboardButton("🧠 مدرسة ICT والسيولة SMC")
    btn3 = types.KeyboardButton("🌊 موجات أليوت والهارمونيك")
    btn4 = types.KeyboardButton("📐 التحليل الرقمي وزوايا جان")
    btn5 = types.KeyboardButton("🎯 القيمة العادلة والدعم/المقاومة")
    btn6 = types.KeyboardButton("📅 التقويم وإجازات الأسواق")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "📈 *أهلاً بك في محرك التحليل الشامل - أكاديمية سمو الأرقام (SMU)*\n\n"
        "تم دمج **جميع مدارس التحليل الفني والمالي العالمية** في منصة واحدة:\n"
        "• 🌊 **موجات أليوت** ونماذج **الهارمونيك** (يومي / أسبوعي)\n"
        "• 🧠 **مدرسة ICT** وكتل الأوامر ($Order\\ Blocks$) والسيولة\n"
        "• 📐 **التحليل الرقمي وزوايا جان** لمربع التسعة\n"
        "• 🎯 **مناطق العرض والطلب** والقيمة المستهدفة\n"
        "• 📊 **المدرسة الكلاسيكية** والمؤشرات الفنية\n\n"
        "💬 *أرسل رمز أي سهم مباشرة (مثال: `2222` أو `NVDA`) أو اختر من القائمة:* "
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text == "📅 التقويم وإجازات الأسواق")
def calendar_info(message):
    cal_text = (
        "📅 *التقويم وإجازات الأسواق المالية*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🇸🇦 *السوق السعودي (تداول):*\n"
        "• أيام العمل: الأحد إلى الخميس (10:00 ص - 3:00 م)\n"
        "• الإجازة: الجمعة والسبت\n\n"
        "🇺🇸 *السوق الأمريكي (US Markets):*\n"
        "• أيام العمل: الاثنين إلى الجمعة (4:30 م - 11:00 م بتوقيت مكة)\n"
        "• الإجازة: السبت والأحد"
    )
    bot.send_message(message.chat.id, cal_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text in [
    "🌐 التحليل الموحد (كل مدارس التحليل)", 
    "🧠 مدرسة ICT والسيولة SMC", 
    "🌊 موجات أليوت والهارمونيك", 
    "📐 التحليل الرقمي وزوايا جان", 
    "🎯 القيمة العادلة والدعم/المقاومة"
])
def prompt_symbol(message):
    bot.reply_to(message, "💬 اكتب رمز السهم المطلوب (مثال: `2222` أو `AAPL`):", parse_mode='Markdown')

# حساب المؤشرات الكلاسيكية
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs)).iloc[-1], 2)

@bot.message_handler(func=lambda message: True)
def process_comprehensive_analysis(message):
    symbol_input = message.text.strip().upper()
    if symbol_input.startswith('/'):
        return

    ticker_symbol = f"{symbol_input}.SR" if symbol_input.isdigit() else symbol_input

    try:
        stock = yf.Ticker(ticker_symbol)
        # جلب البيانات التاريخية المباشرة تفادياً لحظر Yahoo 401
        hist = stock.history(period="120d")

        if hist.empty:
            bot.reply_to(message, f"❌ تعذر جلب بيانات السهم `{symbol_input}`. تأكد من صحة الرمز.", parse_mode='Markdown')
            return

        # 1. البيانات الأساسية والكلاسيكية
        close_p = round(hist['Close'].iloc[-1], 2)
        prev_close = round(hist['Close'].iloc[-2], 2) if len(hist) > 1 else close_p
        change = round(close_p - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2)
        currency = "SAR" if symbol_input.isdigit() else "USD"
        
        rsi = calculate_rsi(hist)
        ema20 = round(hist['Close'].ewm(span=20, adjust=False).mean().iloc[-1], 2)
        ema50 = round(hist['Close'].ewm(span=50, adjust=False).mean().iloc[-1], 2)

        # 2. مدرسة ICT والسيولة والعرض/الطلب (SMC)
        ob_demand = round(hist['Low'].tail(20).min(), 2)
        ob_supply = round(hist['High'].tail(20).max(), 2)
        fvg_level = round((ob_demand + close_p) / 2, 2)

        # 3. موجات أليوت والهارمونيك
        wave_status = "الموجة 3 الصاعدة (امتدادية)" if close_p > ema20 > ema50 else "الموجة C (تصحيحية)"
        diff = ob_supply - ob_demand
        harmonic_0618 = round(close_p + (diff * 0.618), 2)

        # 4. التحليل الرقمي وزوايا جان
        sqrt_p = math.sqrt(close_p)
        gann_90 = round((sqrt_p + 0.5)**2, 2)
        gann_180 = round((sqrt_p + 1.0)**2, 2)

        # 5. التقييم المالي الرقمي
        pivot = round((hist['High'].iloc[-1] + hist['Low'].iloc[-1] + close_p) / 3, 2)
        fair_value_est = round((close_p + gann_180 + pivot) / 3, 2)

        # رسم الشارت
        buf = io.BytesIO()
        mpf.plot(hist.tail(40), type='candle', style='charles', savefig=buf)
        buf.seek(0)

        # صياغة التتقرير الكلي الموحد
        report = (
            f"🏛️ *تقرير التحليل الشامل الموحد - أكاديمية سمو الأرقام*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ *السهم:* `{symbol_input}` | *السعر الحالي:* `{close_p}` {currency}\n"
            f"⚡ *التغير اليومي:* `{change:+}` ({change_pct:+}%)\n\n"

            f"📊 *1. المدرسة الكلاسيكية والمؤشرات:*\n"
            f"• *مؤشر RSI:* `{rsi}` | *EMA 20:* `{ema20}` | *EMA 50:* `{ema50}`\n\n"

            f"🧠 *2. مدرسة ICT والسيولة (SMC):*\n"
            f"🟢 *منطقة الطلب (Order Block):* `{ob_demand}`\n"
            f"🔴 *منطقة العرض (Supply Zone):* `{ob_supply}`\n"
            f"⚡ *فجوة القيمة العادلة (FVG):* `{fvg_level}`\n\n"

            f"🌊 *3. موجات أليوت والهارمونيك:*\n"
            f"• *ترقيم أليوت المرجح:* `{wave_status}`\n"
            f"🎯 *هدف الهارمونيك (0.618 Fib):* `{harmonic_0618}` {currency}\n\n"

            f"📐 *4. التحليل الرقمي وزوايا جان (SMU Geometry):*\n"
            f"• *زاوية 90°:* `{gann_90}` | *زاوية 180°:* `{gann_180}` {currency}\n\n"

            f"🎯 *5. النقطة المحورية والقيمة العادلة التقديرية:*\n"
            f"• *النقطة المحورية (Pivot):* `{pivot}` {currency}\n"
            f"• *القيمة العادلة المستهدفة:* `{fair_value_est}` {currency}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✨ *أكاديمية سمو الأرقام لعلوم التداول*"
        )

        bot.send_photo(message.chat.id, photo=buf, caption=report, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, "⚠️ حدث خطأ أثناء إجراء التحليل الشامل.")

if __name__ == '__main__':
    bot.infinity_polling()
