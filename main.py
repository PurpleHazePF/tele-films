import telebot
import imdb
from config import apytoken
from films_info import find_film

bot = telebot.TeleBot(apytoken)
moviesDB = imdb.IMDb()


@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "Какой фильм вы бы хотели посмотреть")


@bot.message_handler(commands=['find'])
def get_film(m):
    f_name = ''.join(m.text.split()[1:])
    req = find_film(f_name)
    poster = open('poster.jpg', 'rb')
    bot.send_photo(m.chat.id, poster)
    bot.send_message(m.chat.id, req.format(m.from_user, bot.get_me()), parse_mode='html')


bot.polling(none_stop=True, interval=0)
