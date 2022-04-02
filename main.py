import telebot
from telebot import types
import imdb
from config import apytoken
from films_info import find_film
from actors_info import find_person
from data.users import Film, User
from data.db_session import global_init, create_session
import wikipedia

language = "ru"
wikipedia.set_lang(language)
bot = telebot.TeleBot(apytoken)
moviesDB = imdb.IMDb()
localdb = 'db/films_info'
global_init(localdb)
current_film = 0


@bot.message_handler(commands=['start'])
def start(m):
    db_sess = create_session()
    user = User()
    user.tg_id = m.join['from']['id']
    db_sess.add(user)
    db_sess.commit()
    bot.send_message(m.chat.id, "Какой фильм вы бы хотели посмотреть")


@bot.message_handler(commands=['film'])
def get_film(m):
    f_name = ''.join(m.text.split()[1:])
    req = find_film(f_name, m.json['from']['id'])
    poster = open('poster.jpg', 'rb')
    keyboard1 = types.InlineKeyboardMarkup(row_width=3)
    button1 = types.InlineKeyboardButton('Оценить', callback_data=f'q1{req[1]}')  # в названии кнопки хранится
    button2 = types.InlineKeyboardButton('Подробнее', callback_data=f'q2{req[1]}')  # id фильма к которому она привязана
    button3 = types.InlineKeyboardButton('Актёры', callback_data=f'q3{req[1]}')
    button4 = types.InlineKeyboardButton('Буду смотреть', callback_data=f'q4{req[1]}')
    keyboard1.add(button1, button2, button3, button4)
    bot.send_photo(m.chat.id, poster)
    bot.send_message(m.chat.id, req[0].format(m.from_user, bot.get_me()), parse_mode='html', reply_markup=keyboard1)


@bot.message_handler(commands=['person'])
def get_person(m):
    p_name = ' '.join(m.text.split()[1:])
    req = find_person(p_name)
    poster = open('poster.jpg', 'rb')
    bot.send_photo(m.chat.id, poster)
    bot.send_message(m.chat.id, req)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        if call.message:
            if call.data[:1] == 'q':
                if call.data[:2] == 'q1':
                    global current_film
                    current_film = int(call.data[2:])
                    bot.send_message(call.message.chat.id, 'Какова ваша оценка?')
                    bot.register_next_step_handler(call.message, get_rating)
                elif call.data[:2] == 'q2':
                    page = wikipedia.summary(f'ID {call.data[2:]}')  # инфа о фильме с wikipedia
                    bot.send_message(call.message.chat.id, page)
                elif call.data[:2] == 'q4':
                    db_sess = create_session()
                    curr_id = int(call.data[2:])
                    fm = db_sess.query(Film).filter(Film.film_id == curr_id)[0]
                    fm.watch_list = True
                    title = fm.loc_title
                    db_sess.commit()
                    bot.send_message(call.message.chat.id, f'Фильм "{title}" добавлен в лист ожидания')
                elif call.data[:2] == 'q3':
                    curr_id = int(call.data[2:])
                    film = moviesDB.get_movie(curr_id)
                    text = ''
                    for i, j in enumerate(film['cast']):
                        text += f'{i + 1}) <b>{j}</b>\n'
                    bot.send_message(call.message.chat.id, text.format(call.message.from_user, bot.get_me()),
                                     parse_mode='html')

    except Exception:
        bot.send_message(call.message.chat.id, 'Error callback')


def get_rating(message):
    global current_film
    db_sess = create_session()
    fm_rating = message.text
    try:
        numb = int(fm_rating)
        fm = db_sess.query(Film).filter(Film.film_id == current_film)[0]
        fm.rating = numb
        db_sess.commit()
        bot.send_message(message.chat.id, 'Оценка успешно добавлена')
    except Exception:
        bot.send_message(message.chat.id, 'Некорректная оценка')


bot.polling(none_stop=True, interval=0)
