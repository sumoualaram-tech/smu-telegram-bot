import os
import requests
import feedparser
import yfinance as yf
import pandas_ta as ta
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. خادم Flask لإبقاء الخدمة نشطة على Render ---
app = Flask('')

@app.route('/')
def home():
    return "Complete Financial Bot is Active & Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. متغيرات البيئة ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

last_published_title = ""

# --- 3. النشر التلقائي للأخبار والإعلانات إلى القناة الخاصّة ---
async def auto_post_news(context: ContextTypes.DEFAULT_TYPE):
    global last_published_title
    if not CHANNEL_ID:
        return
        
    rss_url = "https://sa.investing.com/rss/news.rss"
    feed = feedparser.parse(rss_url)
    
    if feed.entries:
        latest = feed.entries[0]
        if latest.title != last_published_title:
            last_published_title = latest.title
            
            msg = f"🚨 **إعلان / خبر عاجل:**\n\n"
            msg += f"📢 **{latest.title}**\n\n"
            msg += f"🔗 [اقرأ التفاصيل من المصدر]({latest.link})\n\n"
            msg += "🏛️ *متابعة فورية لأسواق المال*"
            
            try:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=msg,
                    parse_mode='Markdown',
                    disable_web_page_preview=False
                )
            except Exception as e:
                print(f"Error sending to channel: {e}")

# --- 4. أمر إغلاقات الأسواق والسيولة (/market) ---
async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markets = {
        'S&P 500': 'US500',
        'Nasdaq 100': 'US100',
        'Dow Jones': 'US30',
        'Bitcoin': 'BINANCE:BTCUSDT'
    }
    
    report = "🌐 **إغلاقات وحالة الأسواق والسيولة اللحظية:**\n\n"
    
    for name, symbol in markets.items():
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
        try:
            res = requests.get(url).json()
            price = res.get('c', 0)
            change = res.get('d', 0)
            pct_change = res.get('dp', 0)
            
            icon = "🟢" if change >= 0 else "🔴"
            report += f"{icon} **{name}:**\n"
            report += f"   • السعر: `${price:,.2f}`\n"
            report += f"   • التغير: `{change:+.2f}` (`{pct_change:+.2f}%`)\n\n"
        except Exception:
            report += f"⚠️ **{name}:** تعذر جلب البيانات اللحظية.\n\n"
            
    await update.message.reply_text(report, parse_mode='Markdown')

# --- 5. أمر التقرير المالي الشامل + التحليل الرقمي والقيمة العادلة (/stock أو /analyze) ---
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 يرجى كتابة رمز السهم، مثال:\n`/stock AAPL` أو `/analyze NVDA`", parse_mode='Markdown')
        return

    symbol = context.args[0].upper()
    ticker = yf.Ticker(symbol)
    
    # 1. جلب البيانات اللحظية من Finnhub
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    metric_url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={FINNHUB_KEY}"
    target_url = f"https://finnhub.io/api/v1/stock/price-target?symbol={symbol}&token={FINNHUB_KEY}"

    try:
        quote = requests.get(quote_url).json()
        metrics = requests.get(metric_url).json().get('metric', {})
        targets = requests.get(target_url).json()

        price = quote.get('c', 0)
        prev_close = quote.get('pc', 0)

        # 2. البيانات المالية والتوقعات
        pe_ratio = metrics.get('peBasicExclExtraTTM', 'N/A')
        pb_ratio = metrics.get('pbAnnual', 'N/A')
        roe = metrics.get('roeTTM', 'N/A')
        market_cap = metrics.get('marketCapitalization', 0)

        target_mean = targets.get('targetMean', 'N/A')
        target_high = targets.get('targetHigh', 'N/A')
        target_low = targets.get('targetLow', 'N/A')

        # 3. التحليل الرقمي والفني باستخدام pandas-ta
        hist = ticker.history(period="60d")
        rsi_val = "N/A"
        if not hist.empty and len(hist) >= 14:
            rsi_series = ta.rsi(hist['Close'], length=14)
            if rsi_series is not None and not rsi_series.empty:
                rsi_val = f"{rsi_series.iloc[-1]:.2f}"

        report = f"📊 **التقرير الشامل والتحليل الرقمي لـ ({symbol})**\n\n"
        
        report += "💰 **حركة السعر والسيولة اللحظية:**\n"
        report += f"• السعر الحالي: `${price}`\n"
        report += f"• إغلاق الأمس: `${prev_close}`\n\n"
        
        report += "📈 **البيانات المالية:**\n"
        report += f"• القيمة السوقية: `{market_cap:,.0f}M $`\n"
        report += f"• مكرر الربحية (P/E): `{pe_ratio}`\n"
        report += f"• مضاعف القيمة الدفترية (P/B): `{pb_ratio}`\n"
        report += f"• العائد على الملكية (ROE): `{roe}%`\n\n"
        
        report += "🔢 **التحليل الرقمي (Technical Analysis):**\n"
        report += f"• مؤشر القوة النسبية (RSI 14): `{rsi_val}`\n\n"

        report += "🏦 **توقعات البنوك والمحللين (القيمة العادلة المتوقعة):**\n"
        report += f"• المستهدف المتوسط: `${target_mean}`\n"
        report += f"• الأعلى: `${target_high}` | الأدنى: `${target_low}`\n"

        await update.message.reply_text(report, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء جلب البيانات: {str(e)}")

# --- 6. أمر تحليلات الذكاء الاصطناعي (/ai) ---
async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 يرجى كتابة رمز السهم، مثال:\n`/ai AAPL`", parse_mode='Markdown')
        return

    symbol = context.args[0].upper()
    if not OPENAI_KEY:
        await update.message.reply_text("⚠️ ميزة الذكاء الاصطناعي تتطلب ضبط متغير `OPENAI_API_KEY` على Render.")
        return

    await update.message.reply_text(f"🤖 جاري تحليل {symbol} باستخدام الذكاء الاصطناعي...")

    metric_url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={FINNHUB_KEY}"
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    
    metrics = requests.get(metric_url).json().get('metric', {})
    quote = requests.get(quote_url).json()

    prompt = f"قدم تحليلاً مالياً وموجزاً لسهم {symbol} باللغة العربية بناءً على البيانات المالية التالية:\nالسعر: {quote.get('c')}\nمكرر الربحية P/E: {metrics.get('peBasicExclExtraTTM')}\nالعائد على الملكية ROE: {metrics.get('roeTTM')}%"

    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}]
            }
        ).json()

        analysis = res['choices'][0]['message']['content']
        await update.message.reply_text(f"🧠 **تحليل الذكاء الاصطناعي لـ {symbol}:**\n\n{analysis}", parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("❌ تعذر إنشاء تحليل الذكاء الاصطناعي حالياً.")

# --- 7. تشغيل البوت ---
def main():
    Thread(target=run_flask).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("market", market_command))
    application.add_handler(CommandHandler("stock", analyze_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("ai", ai_command))

    # النشر التلقائي كل 10 دقائق (600 ثانية)
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(auto_post_news, interval=600, first=10)

    application.run_polling()

if __name__ == '__main__':
    main()
