import telebot
from config import apytoken

bot = telebot.TeleBot(apytoken)


@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "Какой фильм вы бы хотели посмотреть")


bot.polling(none_stop=True, interval=0)
