import wikipedia

# language = "ru"
# wikipedia.set_lang(language)
# result = wikipedia.search("ID 0133093")
# page = wikipedia.page(result[0])
# content = page.content
# print(content)
# print(wikipedia.summary('ID 0227759'))
# import imdb
#
# moviesDB = imdb.IMDb()
#
# # PeterDinklage IMDB ID
# ActorId = "0227759"
# person = moviesDB.get_person(ActorId)
# # Actor's name
# print(person)
# actor_work = moviesDB.get_person_filmography(ActorId)
# print(actor_work)
# for movie in actor_work['data']['filmography']['actor']:
#     try:
#         print(movie.movieID, movie['title'], movie.currentRole, movie['year'])
#     except KeyError:
#         # print("No Year for the movie")
#         print(movie.movieID, movie['title'], movie.currentRole)
#
# from imdb import Cinemagoer
#
# # create an instance of the Cinemagoer class
# ia = Cinemagoer()
#
# # get a movie and print its director(s)
# the_matrix = ia.get_movie('0133093')
# for director in the_matrix['directors']:
#     print(director['name'])
#
# # show all information that are currently available for a movie
# print(sorted(the_matrix.keys()))
#
# # show all information sets that can be fetched for a movie
# print(ia.get_movie_infoset())
#
# # update a Movie object with more information
# ia.update(the_matrix, ['technical'])
# # show which keys were added by the information set
# print(the_matrix.infoset2keys['technical'])
# # print one of the new keys
# print(the_matrix.get('tech'))
from imdb import IMDb
ia = IMDb()
theMatrix = ia.get_movie('0133093')
print(theMatrix['sound mix'])

