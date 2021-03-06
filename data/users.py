import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    tg_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, unique=True, primary_key=True)
    year = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    genre = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    genre_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    rating = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    film = orm.relation("Film", back_populates='user')


class Film(SqlAlchemyBase):
    __tablename__ = 'info'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    film_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, unique=True)
    kinopoisk_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, unique=True)
    loc_title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    rating = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    viewed = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)
    watch_list = sqlalchemy.Column(sqlalchemy.BOOLEAN, default=False)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    us_tg_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.tg_id"))
    user = orm.relation('User')
