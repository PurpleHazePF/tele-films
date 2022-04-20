import imdb
from kinopoisk_unofficial.kinopoisk_api_client import KinopoiskApiClient
from kinopoisk_unofficial.request.films.film_request import FilmRequest
from kinopoisk.movie import Movie
from kinopoisk_unofficial.request.films.box_office_request import BoxOfficeRequest
import requests
from data.users import Film
from data.db_session import create_session

moviesDB = imdb.IMDb()


def find_film(f_name, user_id):
    try:
        db_sess = create_session()
        api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")  # api token
        movies = moviesDB.search_movie(f_name.lower())  # поиск фильма на imdb
        f_id = movies[0].getID()
        movie = moviesDB.get_movie(f_id)
        movie_list = Movie.objects.search(movie['localized title'])  # поиск фильма на кинопоиске
        id = movie_list[0].id
        request = FilmRequest(id)
        response = api_client.films.send_film_request(request)  # информация о фильме
        url = requests.get(response.film.poster_url)  # постер
        poster = url.content
        f = open('poster.jpg', 'wb')
        f.truncate()
        f.write(bytes(poster))
        f.close()
        if len(db_sess.query(Film).filter(Film.us_tg_id == user_id, Film.film_id == f_id).all()) == 0:
            film = Film()  # если нет такого фильма в дб, то записываем основную информацию
            film.film_id = int(f_id)
            film.kinopoisk_id = id
            film.us_tg_id = int(user_id)
            film.loc_title = movie['localized title']
            film.url = response.film.web_url
            db_sess.add(film)
            db_sess.commit()
        film = db_sess.query(Film).filter(Film.us_tg_id == user_id, Film.film_id == f_id).all()[0]
        request = BoxOfficeRequest(id)
        response2 = api_client.films.send_box_office_request(request)  # поиск инфы о кассовых сборах
        text = f"Название фильма: <b>{movie['localized title']}</b>\n" \
               f"Оригинальное название: <b>{movie['original title']}</b>\n" \
               f"Режиссер: <b>{movie['directors'][0]}</b>\n" \
               f"Актеры: {', '.join([str(i) for j, i in enumerate(movie['cast']) if j < 4])}\n" \
               f"Жанр: {movie['genres'][0]}, {movie['genres'][1]}\nГод выпуска: {movie['year']}\n" \
               f"Рейтинг IMDb: <b>{movie['rating']}</b>\n" \
               f"Страна: {movie['countries'][0]}\n" \
               f"Сценарист: {movie['writers'][0]}\n" \
               f"Бюджет: {response2.items[0].amount}{response2.items[0].symbol}\n" \
               f"Кассовые сборы: {response2.items[2].amount}{response2.items[2].symbol}\n" \
               f"Ваша оценка: {film.rating}\n" \
               f"Ссылка: <a>{response.film.web_url}</a>"
        return text, f_id, id  # отсылаем собранное сообщение и 2 id
    except Exception:
        return ['Error']


def reduced_find_film(f_kn_id):
    try:
        api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")
        request = FilmRequest(f_kn_id)
        response = api_client.films.send_film_request(request)  # поиск фильма на кинопоиске
        text = f"Название фильма: <b>{response.film.name_ru}</b>\n" \
               f"Год выпуска: <b>{response.film.year}</b>\n" \
               f"Жанр: {response.film.genres[0].genre}, {response.film.genres[1].genre}\nГод выпуска: {response.film.year}\n" \
               f"Рейтинг IMDb: <b>{response.film.rating_imdb}</b>\n" \
               f"Рейтинг Кинопоиска: <b>{response.film.rating_kinopoisk}</b>\n" \
               f"Описание: <b>{response.film.short_description}</b>\n" \
               f"Страна: {response.film.countries[0].country}\n"
        url = response.film.web_url
        return text, url  # отсылаем собранное сообщение и id
    except Exception:
        return ['Error']
