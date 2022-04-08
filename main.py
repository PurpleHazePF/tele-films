import telebot
from telebot import types
import imdb
from config import apytoken, trailers
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
    if db_sess.query(User).filter(User.tg_id == m.from_user.id) is None:
        user = User()
        user.tg_id = m.from_user.id
        db_sess.add(user)
        db_sess.commit()
    bot.send_message(m.chat.id, f'Привет {m.from_user.first_name}!')
    bot.send_message(m.chat.id, "Какой фильм вы бы хотели посмотреть")

@bot.message_handler(commands=['help'])
def help(m):
    bot.send_message(m.chat.id, "*Справка по командам:*\n/get_film - /film\n/person - информация о актёре\n/watch_list - список просмотренного", parse_mode="Markdown")


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


@bot.message_handler(commands=['trailer'])
def get_trailer(m):
    film = " ".join(m.text.split()[1:])
    try:
        res = trailers[film.lower()]
        bot.send_message(m.chat.id, f"Трейлер к фильму {film}")
        bot.send_message(m.chat.id, res)
    except Exception:
        bot.send_message(m.chat.id, "Этого трейлера пока нету в нашей базе")
        bot.send_sticker(m.chat.id, "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")


@bot.message_handler(commands=['watch_list'])
def get_watch_list(m):
    user_id = m.from_user.id
    db_sess = create_session()
    user = db_sess.query(User).filter(User.tg_id == user_id)[0]
    films = user.film
    text = ''
    for i, j in enumerate(films):
        if j.watch_list:
            text += f'{i + 1})  <b>{j.loc_title}</b>\n'
    bot.send_message(m.chat.id, text, parse_mode='html')


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
                elif call.data[:2] == 'q3':
                    curr_id = int(call.data[2:])
                    film = moviesDB.get_movie(curr_id)
                    text = ''
                    for i, j in enumerate(film['cast']):
                        text += f'{i + 1}) <b>{j}</b>\n'
                    bot.send_message(call.message.chat.id, text.format(call.message.from_user, bot.get_me()),
                                     parse_mode='html')
                elif call.data[:2] == 'q4':
                    db_sess = create_session()
                    curr_id = int(call.data[2:])
                    fm = db_sess.query(Film).filter(Film.film_id == curr_id)[0]
                    fm.watch_list = True
                    title = fm.loc_title
                    db_sess.commit()
                    bot.send_message(call.message.chat.id, f'Фильм "{title}" добавлен в лист ожидания')

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
        fm.viewed = True
        fm.watch_list = False
        db_sess.commit()
        bot.send_message(message.chat.id, 'Оценка успешно добавлена')
    except Exception:
        bot.send_message(message.chat.id, 'Некорректная оценка')


bot.polling(none_stop=True, interval=0)
