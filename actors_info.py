import imdb
import requests
import wikipedia

language = "ru"
wikipedia.set_lang(language)
moviesDB = imdb.IMDb()


def find_person(p_name):
    movies = moviesDB.search_person(p_name)
    f_id = movies[0].getID()
    person = moviesDB.get_person(f_id)
    p = requests.get(person['full-size headshot'])
    poster = p.content
    f = open('poster.jpg', 'wb')
    f.truncate()
    f.write(bytes(poster))
    f.close()
    return wikipedia.summary(f'ID {f_id}')
