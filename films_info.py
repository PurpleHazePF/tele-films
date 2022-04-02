import imdb
import requests
from data.users import Film
from data.db_session import create_session

moviesDB = imdb.IMDb()


def find_film(f_name, user_id):
    try:
        db_sess = create_session()
        movies = moviesDB.search_movie(f_name.lower())
        f_id = movies[0].getID()
        movie = moviesDB.get_movie(f_id)
        url = requests.get(movie['cover url'])
        poster = url.content
        f = open('poster.jpg', 'wb')
        f.truncate()
        f.write(bytes(poster))
        f.close()
        if len(db_sess.query(Film).filter(Film.us_tg_id == user_id, Film.film_id == f_id).all()) == 0:
            film = Film()
            film.film_id = int(f_id)
            film.us_tg_id = int(user_id)
            film.loc_title = movie['localized title']
            db_sess.add(film)
            db_sess.commit()
        text = f"Название фильма: <b>{movie['localized title']}</b>\n" \
               f"Оригинальное название: <b>{movie['original title']}</b>\n" \
               f"Режиссер: <b>{movie['directors'][0]}</b>\n" \
               f"Актеры: {', '.join([str(i) for j, i in enumerate(movie['cast']) if j < 4])}\n" \
               f"Жанр: {movie['genres'][0]}, {movie['genres'][1]}\nГод выпуска: {movie['year']}\n" \
               f"Рейтинг IMDb: <b>{movie['rating']}</b>\n" \
               f"Страна: {movie['countries'][0]}\n" \
               f"Сценарист: {movie['writers'][0]}"
        return text, f_id
    except Exception as e:
        return f'{e.__class__.__name__}'
