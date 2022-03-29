import imdb
import requests

moviesDB = imdb.IMDb()


def find_film(f_name):
    try:
        movies = moviesDB.search_movie(f_name.lower())
        f_id = movies[0].getID()
        movie = moviesDB.get_movie(f_id)
        url = requests.get(movie['cover url'])
        poster = url.content
        f = open('poster.jpg', 'wb')
        f.truncate()
        f.write(bytes(poster))
        f.close()
        text = f"Название фильма: <b>{movie['localized title']}</b>\n" \
               f"Оригинальное название: <b>{movie['original title']}</b>\n" \
               f"Режиссер: <b>{movie['directors'][0]}</b>\n" \
               f"Актеры: {', '.join([str(i) for j, i in enumerate(movie['cast']) if j < 4])}\n" \
               f"Жанр: {movie['genres'][0]}\nГод выпуска: {movie['year']}\n" \
               f"Рейтинг IMDb: <b>{movie['rating']}</b>\n" \
               f"Страна: {movie['countries'][0]}\n" \
               f"Сценарист: {movie['writers'][0]}"
        return text
    except Exception:
        return 'ERROR'
