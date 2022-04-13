import telebot
from telebot import types
import imdb
from config import apytoken, staff
from films_info import find_film, reduced_find_film
from actors_info import find_person
from data.users import Film, User
from data.db_session import global_init, create_session
import wikipedia
import sqlite3
from kinopoisk.movie import Movie
from kinopoisk_unofficial.kinopoisk_api_client import KinopoiskApiClient
from kinopoisk_unofficial.request.films.related_film_request import RelatedFilmRequest
from kinopoisk_unofficial.request.films.film_video_request import FilmVideoRequest

language = "ru"
wikipedia.set_lang(language)
bot = telebot.TeleBot('5250938790:AAG2GYrugR1Sa-uxWn6MbaybWcof8d_Bgjc')
moviesDB = imdb.IMDb()
localdb = 'db/films_info'
global_init(localdb)
current_film = 0
con = sqlite3.connect('trailers.db', check_same_thread=False)
cur = con.cursor()


@bot.message_handler(commands=['start'])
def start(m):
    db_sess = create_session()
    try:
        pers = db_sess.query(User).filter(User.tg_id == m.from_user.id)[0]
    except Exception:
        user = User()
        user.tg_id = m.from_user.id
        db_sess.add(user)
        db_sess.commit()
    bot.send_message(m.chat.id, f'Привет {m.from_user.first_name}!')
    bot.send_message(m.chat.id, "Какой фильм вы бы хотели посмотреть")


@bot.message_handler(commands=['help'])
def help(m):
    bot.send_message(m.chat.id,
                     "<b>Справка по командам:</b>\n/film - получить фильм\n/person - информация о актёре\n/watch_list - список просмотренного\n/trailer - посмотреть трейлер к фильму",
                     parse_mode='html')


@bot.message_handler(commands=['film'])
def get_film(m):
    f_name = ' '.join(m.text.split()[1:])
    req = find_film(f_name, m.json['from']['id'])
    poster = open('poster.jpg', 'rb')
    keyboard1 = types.InlineKeyboardMarkup(row_width=3)
    button1 = types.InlineKeyboardButton('Оценить', callback_data=f'q1{req[1]}')  # в названии кнопки хранится
    button2 = types.InlineKeyboardButton('Подробнее', callback_data=f'q2{req[1]}')  # id фильма к которому она привязана
    button3 = types.InlineKeyboardButton('Актёры', callback_data=f'q3{req[1]}')
    button4 = types.InlineKeyboardButton('Буду смотреть', callback_data=f'q4{req[1]}')
    button5 = types.InlineKeyboardButton('Трейлер', callback_data=f'q5{req[2]}')
    keyboard1.add(button1, button2, button3, button4, button5)
    bot.send_photo(m.chat.id, poster)
    bot.send_message(m.chat.id, req[0].format(m.from_user, bot.get_me()), parse_mode='html', reply_markup=keyboard1)


@bot.message_handler(commands=['sim_films'])
def get_similar_film(m):
    f_name = ' '.join(m.text.split()[1:])
    movie_list = Movie.objects.search(f_name)
    id = movie_list[0].id
    api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")  # api token
    request = RelatedFilmRequest(id)
    response = api_client.films.send_related_film_request(request)
    im_pool = [types.InputMediaPhoto(i.poster_url) for i in response.items[:5]]
    text_mes = ''
    for i, j in enumerate(response.items[:5]):
        text_mes += f'{i + 1})'
        resp = reduced_find_film(j.film_id)
        text_mes += resp[0]
        text_mes += resp[1]
        text_mes += f'\n\n'
    bot.send_media_group(m.chat.id, im_pool)
    bot.send_message(m.chat.id, text_mes.format(m.from_user, bot.get_me()), parse_mode='html')


@bot.message_handler(commands=['trailer'])
def get_trailer(m):
    film = " ".join(m.text.split()[1:])
    try:
        a = cur.execute(f"""SELECT url FROM trailers
        WHERE name = '{film.lower()}'""").fetchall()[0][0]
        bot.send_message(m.chat.id, f"Трейлер к фильму {film}")
        bot.send_message(m.chat.id, a)
    except Exception:
        bot.send_message(m.chat.id, "Этого трейлера пока нету в нашей базе")
        bot.send_sticker(m.chat.id, "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")


@bot.message_handler(commands=['addtrailer'])
def addtrailer(m):
    if m.from_user.id in staff:
        try:
            a = m.text.split()[1:]
            cur.execute(f"INSERT INTO trailers(name, url) VALUES('{a[0]}', '{a[1]}')")
            con.commit()
            bot.send_message(m.chat.id, f"Фильм {a[0]} успешно добавлен")
        except Exception as error:
            bot.send_message(m.chat.id, f"error:{error}")
    else:
        bot.send_message(m.chat.id, "У вас нет доступа")


@bot.message_handler(commands=['watch_list'])
def get_watch_list(m):
    user_id = m.from_user.id
    db_sess = create_session()
    user = db_sess.query(User).filter(User.tg_id == user_id)[0]
    films = user.film
    text = ''
    for i, j in enumerate(films):
        if j.watch_list:
            text += f'{i + 1})  <b>{j.loc_title}</b>: {j.url}\n'
    bot.send_message(m.chat.id, text, parse_mode='html')


@bot.message_handler(commands=['person'])
def get_person(m):
    p_name = ' '.join(m.text.split()[1:])
    req = find_person(p_name)
    poster = open('poster.jpg', 'rb')
    bot.send_photo(m.chat.id, poster)
    text = req[0] + '\n' + f'<a>{req[1]}</a>'
    bot.send_message(m.chat.id, text, parse_mode='html')


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
                    for i, j in enumerate(film['cast'][:10]):
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
                elif call.data[:2] == 'q5':
                    api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")
                    request = FilmVideoRequest(int(call.data[2:]))
                    response = api_client.films.send_film_video_request(request)
                    tr_url = ''
                    for i in response.items:
                        if 'дублированный' in i.name and 'youtube' in str(i.url):
                            tr_url = i.url
                            break
                    if tr_url == '':
                        for j in response.items:
                            if 'Трейлер' in str(j.name):
                                tr_url = j.url
                                break
                    if tr_url == '':
                        bot.send_message(call.message.chat.id, 'Мы не смогли найти трейлер')
                        bot.send_sticker(call.message.chat.id,
                                         "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")
                    else:
                        text = f'Трейлер: <a>{tr_url}</a>'
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
        fm.viewed = True
        fm.watch_list = False
        db_sess.commit()
        bot.send_message(message.chat.id, 'Оценка успешно добавлена')
    except Exception:
        bot.send_message(message.chat.id, 'Некорректная оценка')


bot.polling(none_stop=True, interval=0)
