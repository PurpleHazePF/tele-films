import imdb
import requests
import wikipedia
from kinopoisk_unofficial.kinopoisk_api_client import KinopoiskApiClient
from kinopoisk_unofficial.request.staff.person_request import PersonRequest
from kinopoisk.movie import Movie

language = "ru"
wikipedia.set_lang(language)
moviesDB = imdb.IMDb()
api_client = KinopoiskApiClient("74c7edf5-27c8-4dd1-99ae-a96b22f7457a")


def find_person(p_name):
    try:
        person = Movie.objects.search(p_name)
        id = person[0].id
        request = PersonRequest(id)
        response = api_client.staff.send_person_request(request)
        p = requests.get(response.posterUrl)
        poster = p.content
        f = open('poster.jpg', 'wb')
        f.truncate()
        f.write(bytes(poster))
        f.close()
        return wikipedia.summary(f'{response.nameRu}'), response.webUrl
    except Exception:
        return ['Error']
