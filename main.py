import os
import telebot
from telebot import types

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_saudi = types.InlineKeyboardButton("🇸🇦 قناة السوق السعودي", url="https://t.me/your_saudi_channel")
    btn_usa = types.InlineKeyboardButton("🇺🇸 قناة السوق الأمريكي", url="https://t.me/your_usa_channel")
    btn_site = types.InlineKeyboardButton("🌐 موقع أكاديمية سمو الأرقام", url="https://sumoualarqam.com/")

    markup.add(btn_saudi, btn_usa, btn_site)

    welcome_text = (
        "مرحباً بك في بوت *أكاديمية سمو الأرقام (SMU)* 📊✨\n\n"
        "الوجهة الاحترافية للتحليل المالي والإشارات الذهبية.\n"
        "يرجى اختيار أحد الخيارات أدناه للمتابعة:"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

if __name__ == '__main__':
    bot.polling(none_stop=True)
