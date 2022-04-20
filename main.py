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
from random import choice, randint
import datetime
import logging
from kinopoisk.movie import Movie
from kinopoisk_unofficial.kinopoisk_api_client import KinopoiskApiClient
from kinopoisk_unofficial.request.films.related_film_request import RelatedFilmRequest
from kinopoisk_unofficial.request.films.film_video_request import FilmVideoRequest
from kinopoisk_unofficial.request.staff.person_request import PersonRequest
from kinopoisk_unofficial.model.filter_order import FilterOrder
from kinopoisk_unofficial.model.filter_genre import FilterGenre
from kinopoisk_unofficial.request.films.film_search_by_filters_request import FilmSearchByFiltersRequest
from kinopoisk_unofficial.request.films.filters_request import FiltersRequest
from kinopoisk_unofficial.request.films.film_sequels_and_prequels_request import FilmSequelsAndPrequelsRequest
from kinopoisk_unofficial.request.films.facts_request import FactsRequest

# настроки баз данных и библиотек
language = "ru"
wikipedia.set_lang(language)
bot = telebot.TeleBot('5250938790:AAG2GYrugR1Sa-uxWn6MbaybWcof8d_Bgjc')
moviesDB = imdb.IMDb()
localdb = 'db/films_info'
global_init(localdb)
current_film = 0
con = sqlite3.connect('trailers.db', check_same_thread=False)
cur = con.cursor()
logging.basicConfig(
    filename='bot_logs.log',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO)


@bot.message_handler(commands=['start'])
def start(m, flag=0):
    db_sess = create_session()
    try:
        pers = db_sess.query(User).filter(User.tg_id == m.from_user.id)[0]
    except Exception as x:  # если нет такого пользователя, то регестрируем его
        user = User()
        user.tg_id = m.from_user.id
        db_sess.add(user)
        db_sess.commit()
        logging.error(f"Пользователь {m.from_user.username} вызвал ошибку {x}")
    bot.send_message(m.chat.id, f'Привет {m.from_user.first_name}!')
    bot.send_message(m.chat.id, "Какой фильм вы бы хотели посмотреть")


@bot.message_handler(commands=['help'])
def help(m):
    bot.send_message(m.chat.id,
                     "<b>Справка по командам:</b>\n/film - получить фильм\n"
                     "/person - информация о актёре\n/watch_list - список просмотренного\n"
                     "/trailer - посмотреть трейлер к фильму\n/recommend - рекомендация фильмов\n"
                     "/sim_films - поиск похожих фильмов",
                     parse_mode='html')


@bot.message_handler(commands=['film'])
def get_film(m, flag=0):
    try:
        if flag == 1:
            f_name = ' '.join(m.text.split()[2:])
        else:
            f_name = ' '.join(m.text.split()[1:])
        req = find_film(f_name, m.json['from']['id'])
        if req[0] != 'Error':
            poster = open('poster.jpg', 'rb')
            # создаем клавиатуру и кнопки
            keyboard1 = types.InlineKeyboardMarkup(row_width=3)
            button1 = types.InlineKeyboardButton('Оценить', callback_data=f'q1{req[1]}')  # в названии кнопки хранится
            button2 = types.InlineKeyboardButton('Подробнее',
                                                 callback_data=f'q2{req[1]}')  # id фильма к которому она привязана
            button3 = types.InlineKeyboardButton('Актёры', callback_data=f'q3{req[1]}')
            button4 = types.InlineKeyboardButton('Буду смотреть', callback_data=f'q4{req[1]}')
            button5 = types.InlineKeyboardButton('Трейлер', callback_data=f'q5{req[2]}')
            button6 = types.InlineKeyboardButton('Спин-оффы', callback_data=f'q6{req[2]}')
            keyboard1.add(button1, button2, button3, button4, button5, button6)
            bot.send_photo(m.chat.id, poster)
            bot.send_message(m.chat.id, req[0].format(m.from_user, bot.get_me()), parse_mode='html',
                             reply_markup=keyboard1)
        else:
            bot.send_message(m.chat.id, "Ничего не найдено")
            bot.send_sticker(m.chat.id, "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")
    except Exception as x:
        logging.error(f"Пользователь {m.from_user.username} вызвал ошибку {x}")
        bot.send_message(m.chat.id, "Произошла ошибка")
        bot.send_sticker(m.chat.id, "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")


@bot.message_handler(commands=['recommend'])
def get_recommendation_film(m):
    bot.send_message(m.chat.id, 'Фильм с какого года вы бы хотели посмотреть?')
    bot.register_next_step_handler(m, get_year)  # ожидание следующего шага


def get_year(m):
    y = m.text
    if y in ['без разници', 'на ваше усмотрение', 'любой']:
        y = randint(1950, datetime.date.today().year)
    else:
        try:
            y = int(y)
            if y < 1896:  # первый фильм снят в 1896, следовательно год должен быть больше чем 1896
                raise ValueError
        except ValueError:  # если год не является числом, выбираем случайное
            y = randint(1950, datetime.date.today().year)
            print(y)
            bot.send_message(m.chat.id, 'Вы ввели некорректный год, поэтому я выбрал его за вас')
    db_sess = create_session()
    user = db_sess.query(User).filter(User.tg_id == m.from_user.id).all()[0]
    user.year = y
    db_sess.commit()
    bot.send_message(m.chat.id, 'Какой жанр вы предпочитаете?')
    bot.register_next_step_handler(m, get_genre)  # ожидание следующего шага


def get_genre(m):
    api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")  # api token
    request = FiltersRequest()
    response = api_client.films.send_filters_request(request)  # поиск id жанров
    pool = [(i.id, i.genre) for i in response.genres if i.genre.lower() == m.text.lower()]
    if len(pool) > 0:  # если выбраный жанр существует
        genre = pool[0]
    else:
        rand_genre = choice(response.genres)  # если нет, то выбираем случайный
        genre = (rand_genre.id, rand_genre.genre)
        bot.send_message(m.chat.id, 'такого жанра не нашлось, поэтому я выбрал случайный')
    db_sess = create_session()
    user = db_sess.query(User).filter(User.tg_id == m.from_user.id).all()[0]
    user.genre = genre[1]  # записываем информацию в дб
    user.genre_id = genre[0]
    db_sess.commit()
    bot.send_message(m.chat.id, 'Какая минимальная оценка должна быть у этого фильма?')
    bot.register_next_step_handler(m, get_min_rating)  # ожидание следующего шага


def get_min_rating(m):
    try:
        rating = float(m.text)  # проверяем корректность ввода
    except ValueError:
        rating = 5.5
        bot.send_message(m.chat.id, 'Вы ввели некорректную оценку, по умолчанию оценка >= 5.5')
    db_sess = create_session()
    user = db_sess.query(User).filter(User.tg_id == m.from_user.id).all()[0]
    user.rating = rating
    db_sess.commit()
    try:
        api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")  # api token
        request = FilmSearchByFiltersRequest()  # заполняем фильтр поиска
        request.year_from = user.year
        request.rating_from = user.rating
        request.order = FilterOrder.RATING
        request.add_genre(FilterGenre(user.genre_id, genre=user.genre))
        response = api_client.films.send_film_search_by_filters_request(request)  # получаем список фильмов
        im_pool = [types.InputMediaPhoto(i.poster_url) for i in response.items[:5]]  # создаем группу постеров
        text_mes = ''
        for i, j in enumerate(response.items[:5]):
            text_mes += f'{i + 1})'  # заполняем текстовую инфу + ссылки
            resp = reduced_find_film(j.kinopoisk_id)
            text_mes += resp[0]
            text_mes += resp[1]
            text_mes += f'\n\n'
        bot.send_media_group(m.chat.id, im_pool)
        bot.send_message(m.chat.id, text_mes.format(m.from_user, bot.get_me()), parse_mode='html')  # итоговое сообщение
    except Exception as e:
        print(e)
        bot.send_message(m.chat.id, "Произошла ошибка")
        bot.send_sticker(m.chat.id, "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")


@bot.message_handler(commands=['sim_films'])
def get_similar_film(m, flag=0):
    try:
        if flag == 1:  # если функция была вызвана из текстового обработчика
            f_name = ' '.join(m.text.split()[4:])  # название фильма
        else:
            f_name = ' '.join(m.text.split()[1:])  # название фильма
        movie_list = Movie.objects.search(f_name)
        id = movie_list[0].id  # поиск id фильма
        api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")  # api token
        request = RelatedFilmRequest(id)
        response = api_client.films.send_related_film_request(request)  # поиск похожих фильмов
        im_pool = [types.InputMediaPhoto(i.poster_url) for i in response.items[:5]]  # создаем группу постеров
        text_mes = ''
        for i, j in enumerate(response.items[:5]):
            text_mes += f'{i + 1})'  # заполняем текстовую инфу + ссылки
            resp = reduced_find_film(j.film_id)
            text_mes += resp[0]
            text_mes += resp[1]
            text_mes += f'\n\n'
        bot.send_media_group(m.chat.id, im_pool)
        bot.send_message(m.chat.id, text_mes.format(m.from_user, bot.get_me()), parse_mode='html')  # итоговое сообщение
    except Exception as x:
        logging.error(f"Пользователь {m.from_user.username} вызвал ошибку {x}")
        bot.send_message(m.chat.id, "Произошла ошибка")
        bot.send_sticker(m.chat.id, "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")


@bot.message_handler(commands=['trailer'])
def get_trailer(m):
    film = " ".join(m.text.split()[1:])
    try:
        a = cur.execute(f"""SELECT url FROM trailers
        WHERE name = '{film.lower()}'""").fetchall()[0][0]
        bot.send_message(m.chat.id, f"Трейлер к фильму {film}")
        bot.send_message(m.chat.id, a)
    except Exception as x:
        logging.error(f"Пользователь {m.from_user.username} вызвал ошибку {x}")
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
            logging.error(f"Пользователь {m.from_user.username} вызвал ошибку {error}")
            bot.send_message(m.chat.id, f"error:{error}")
    else:
        bot.send_message(m.chat.id, "У вас нет доступа")


@bot.message_handler(commands=['watch_list'])
def get_watch_list(m):
    user_id = m.from_user.id
    db_sess = create_session()
    user = db_sess.query(User).filter(User.tg_id == user_id)[0]  # список фильмов в закладках
    films = [i for i in user.film if i.watch_list]
    text = ''
    for i, j in enumerate(films):
        if j.watch_list:
            text += f'{i + 1})  <b>{j.loc_title}</b>: {j.url}\n'
    bot.send_message(m.chat.id, text, parse_mode='html')  # номеруем и отправляем с ссылкой на кинопоиск


@bot.message_handler(commands=['person'])
def get_person(m, flag=0):
    try:
        if flag == 1:  # если функция была вызвана из текстового обработчика
            p_name = ' '.join(m.text.split()[2:])  # имя человека
        else:
            p_name = ' '.join(m.text.split()[1:])  # имя человека
        req = find_person(p_name)
        if req[0] != 'Error':
            poster = open('poster.jpg', 'rb')  # постер
            bot.send_photo(m.chat.id, poster)
            text = req[0] + '\n' + f'<a>{req[1]}</a>'  # текстовая информация + ссылка
            bot.send_message(m.chat.id, text, parse_mode='html')
        else:
            bot.send_message(m.chat.id, "Такой человек не найден")
            bot.send_sticker(m.chat.id, "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")
    except Exception as x:
        logging.error(f"Пользователь {m.from_user.username} вызвал ошибку {x}")
        bot.send_message(m.chat.id, "Произошла ошибка")
        bot.send_sticker(m.chat.id, "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        if call.message:
            if call.data[:1] == 'q':
                # определяем вид кнопки
                if call.data[:2] == 'q1':
                    global current_film
                    current_film = int(call.data[2:])  # id фильма к которому привязана кнопка
                    bot.send_message(call.message.chat.id, 'Какова ваша оценка?')
                    bot.register_next_step_handler(call.message, get_rating)  # ожидание следующего шага
                elif call.data[:2] == 'q2':
                    page = wikipedia.summary(f'ID {call.data[2:]}')  # инфа о фильме с wikipedia
                    bot.send_message(call.message.chat.id, page)
                elif call.data[:2] == 'q3':
                    api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")
                    curr_id = int(call.data[2:])  # id фильма к которому привязана кнопка
                    film = moviesDB.get_movie(curr_id)
                    text = ''
                    for i, j in enumerate(film['cast'][:10]):
                        if i < 5:  # для первых 5 акеров пытаемся получить ссылку на кинопоиск
                            try:
                                person = Movie.objects.search(str(j))
                                id = person[0].id
                                request = PersonRequest(id)
                                response = api_client.staff.send_person_request(request)  # информация об актёре
                                text += f'{i + 1}) <a href="{response.webUrl}">{j}</a>\n'
                            except Exception as e:
                                text += f'{i + 1}) <b>{j}</b>\n'
                        else:
                            text += f'{i + 1}) <b>{j}</b>\n'  # всех остальных просто перечисляем
                    bot.send_message(call.message.chat.id, text.format(call.message.from_user, bot.get_me()),
                                     parse_mode='html')
                elif call.data[:2] == 'q4':
                    db_sess = create_session()
                    curr_id = int(call.data[2:])  # id фильма к которому привязана кнопка
                    fm = db_sess.query(Film).filter(Film.film_id == curr_id)[0]
                    fm.watch_list = True  # ищем фильм в дб и добавляем watch_list статус
                    title = fm.loc_title
                    db_sess.commit()
                    bot.send_message(call.message.chat.id, f'Фильм "{title}" добавлен в лист ожидания')
                elif call.data[:2] == 'q5':
                    api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")
                    request = FilmVideoRequest(int(call.data[2:]))  # id фильма к которому привязана кнопка
                    response = api_client.films.send_film_video_request(request)  # получаем список трейлеров
                    tr_url = ''
                    for i in response.items:
                        if 'дублированный' in i.name and 'youtube' in str(i.url):
                            tr_url = i.url  # ищем дублированный и русской трейлер
                            break
                    if tr_url == '':
                        for j in response.items:
                            if 'Трейлер' in str(j.name):
                                tr_url = j.url  # если нужного нет, то выбираем любой
                                break
                    if tr_url == '':
                        bot.send_message(call.message.chat.id, 'Мы не смогли найти трейлер')
                        bot.send_sticker(call.message.chat.id,
                                         "CAACAgIAAxkBAAEEaChiUBeRMyt-o2uxOc1mvJSIsUgKAAPZFwACq_whStzEfsp_ztIeIwQ")
                    else:
                        text = f'Трейлер: <a>{tr_url}</a>'  # отправляем ссылку
                        bot.send_message(call.message.chat.id, text.format(call.message.from_user, bot.get_me()),
                                         parse_mode='html')
                elif call.data[:2] == 'q6':
                    api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")
                    try:
                        request = FilmSequelsAndPrequelsRequest(
                            int(call.data[2:]))  # id фильма к которому привязана кнопка
                        response = api_client.films.send_film_sequels_and_prequels_request(
                            request)  # поиск сиквелов и приквелов
                        im_pool = [types.InputMediaPhoto(i.poster_url) for i in response.items[:5]]
                        text_mes = ''
                        for i, j in enumerate(response.items):
                            text_mes += f'{i + 1})'  # оформляем аналогично функции get_similar_film
                            resp = reduced_find_film(j.film_id)
                            text_mes += resp[0]
                            text_mes += resp[1]
                            text_mes += f'\n\n'
                        bot.send_media_group(call.message.chat.id, im_pool)
                        bot.send_message(call.message.chat.id, text_mes.format(call.message.from_user, bot.get_me()),
                                         parse_mode='html')
                    except Exception as e:
                        if e.__class__.__name__ == 'NotFound':
                            bot.send_message(call.message.chat.id, 'Спин-оффов не найдено')
                        else:
                            bot.send_message(call.message.chat.id, 'Произошла ошибка')
                            print(e.__class__.__name__)
    except Exception as x:
        logging.error(f"Пользователь {call.from_user.username} вызвал ошибку {x}")
        bot.send_message(call.message.chat.id, 'Error callback')


def get_rating(message):
    global current_film
    db_sess = create_session()
    fm_rating = message.text
    try:  # устанавливаем в дб новый рейтинг
        numb = int(fm_rating)
        fm = db_sess.query(Film).filter(Film.film_id == current_film)[0]
        fm.rating = numb
        fm.viewed = True
        fm.watch_list = False
        db_sess.commit()
        bot.send_message(message.chat.id, 'Оценка успешно добавлена')
    except Exception:
        bot.send_message(message.chat.id, 'Некорректная оценка')


@bot.message_handler(content_types='text')
def lis_text(m):
    word_of_search_film = ['найди фильм', 'покажи фильм', 'опиши фильм', 'скинь фильм']
    word_of_search_actor = ['найди актера', 'покажи актера', 'опиши актера']
    word_welcome = ['привет', 'здавствуй', 'приветствую']
    word_of_search_sim_film = ['найди похожие фильмы на', 'покажи фильмы похожие на', 'найди фильм похожий на']
    help_word = ['что ты умеешь', "что ты можешь", "что можешь", "на что ты способен", "на что ты годен"]
    if len(list(filter(lambda x: x in m.text.lower(), word_of_search_film))) > 0:
        get_film(m, flag=1)
    elif len(list(filter(lambda x: x in m.text.lower(), word_of_search_actor))) > 0:
        get_person(m, flag=1)
    elif len(list(filter(lambda x: x in m.text.lower(), word_of_search_sim_film))) > 0:
        get_similar_film(m, flag=1)
    elif len(list(filter(lambda x: x == m.text.lower().split()[0], word_welcome))) > 0:
        start(m, flag=1)
    elif len(list(filter(lambda x: x in m.text.lower(), help_word))) > 0:
        help(m)
    else:
        db_sess = create_session()
        api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")
        fm = db_sess.query(Film).filter(Film.us_tg_id == m.from_user.id)[0]
        request = FactsRequest(fm.kinopoisk_id)
        response = api_client.films.send_facts_request(request)
        fact = choice(response.items)
        bot.send_message(m.chat.id, 'Я вас не понимаю')
        bot.send_message(m.chat.id, f'Вот вам факт о фильме <b>"{fm.loc_title}"</b>', parse_mode='html')
        bot.send_message(m.chat.id, fact.text, parse_mode='html')


bot.polling(none_stop=True, interval=0)
