import sqlite3
import json
import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
import uuid
from dataclasses import dataclass, field
from typing import List, Set, Union
from loguru import logger

# logging.basicConfig(filename="sample.log", level=logging.INFO)


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    '''
    Так как в SQLite нет встроенной фабрики для строк в виде dict,
    всё приходится делать самостоятельно
    '''
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@dataclass
class Person:
    id: str = field(default=None)
    id_pg: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = field(default=None)


@dataclass
class Genres:
    id_pg: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = field(default=None)


@dataclass
class Movie:
    id: str
    genre: str = None
    writer: str = None
    writers: str = None
    director: str = None
    title: str = field(default=None)
    plot: str = field(default=None)
    ratings: str = field(default=None)
    imdb_rating: str = field(default=None)
    id_pg: uuid.UUID = field(default_factory=uuid.uuid4)
    director_list: Set[uuid.UUID] = field(default_factory=set)
    writer_list: Set[uuid.UUID] = field(default_factory=set)
    genre_list: Set[uuid.UUID] = field(default_factory=set)
    actor_list: Set[uuid.UUID] = field(default_factory=set)


class SQLiteLoader:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = dict_factory
        self.movie_list: List[Movie] = []
        self.movie_set: Set[str] = set()
        self.genre_list: List[Genres] = []
        self.person_list: List[Person] = []
        self.person_set: Set[str] = set()

    def _load_writers(self):
        for writer_dict in self.conn.execute('select * from writers'):
            if writer_dict['name'] == 'N/A':
                continue
            writer = Person(**writer_dict)
            self.person_list.append(writer)
            self.person_set.add(writer.id)

    def _load_actors(self):
        for actors_dict in self.conn.execute('select * from actors'):
            if actors_dict['name'] == 'N/A':
                continue
            actor = Person(name=actors_dict['name'], id=str(actors_dict['id']))
            self.person_list.append(actor)
            self.person_set.add(actor.id)

    def _load_movies(self):
        movie_actor_db = []
        for m_a in self.conn.execute(f'select * from movie_actors'):
            movie_actor_db.append(m_a)
        for movie_dict in self.conn.execute('select * from movies'):
            movie = Movie(**movie_dict)
            if movie.director != 'N/A':
                directors = movie.director.split(', ')
                for name_director in directors:
                    director = self._search_person_with_name(name=name_director)
                    if director:
                        movie.director_list.add(director.id_pg)
                    else:
                        director = Person(name=name_director)
                        self.person_list.append(director)
                        movie.director_list.add(director.id_pg)

            if movie.writer != 'N/A':
                writer = self._search_person_with_id(id_=movie.writer)
                if writer:
                    movie.writer_list.add(writer.id_pg)
            if movie.writers != '':
                for writer_id in json.loads(movie.writers):
                    writer = self._search_person_with_id(id_=writer_id)
                    if writer:
                        movie.writer_list.add(writer.id_pg)

            genre_list = movie.genre.split(', ')
            for genre_name in genre_list:
                genre = self._search_genre_with_name(name=genre_name)
                if genre:
                    movie.genre_list.add(genre.id_pg)
                else:
                    genre = Genres(name=genre_name)
                    self.genre_list.append(genre)
                    movie.genre_list.add(genre.id_pg)

            for movie_actor_dict in movie_actor_db:
                if movie_actor_dict["movie_id"] == movie.id:
                    actor = self._search_person_with_id(id_=str(movie_actor_dict["actor_id"]))
                    if actor:
                        movie.actor_list.add(actor.id_pg)
            self.movie_list.append(movie)

    def _search_movie_with_id(self, id_: str) -> Union[Movie, bool]:
        for movie in self.movie_list:
            if movie.id == id_:
                return movie
        return False

    def _search_person_with_id(self, id_: str) -> Union[Person, bool]:
        if str(id_) in self.person_set:
            for person in self.person_list:

                if person.id == id_:
                    return person
        return False

    def _search_genre_with_name(self, name: str) -> Union[Genres, bool]:
        for genre in self.genre_list:
            if genre.name == name:
                return genre
        return False

    def _search_person_with_name(self, name: str) -> Union[Person, bool]:
        for person in self.person_list:
            if person.name == name:
                return person
        return False

    def load_movies(self) -> dict:
        self._load_actors()
        self._load_writers()
        self._load_movies()

        data = {
            "movies": self.movie_list,
            "persons": self.person_list,
            "genre": self.genre_list
        }
        return data


class PostgresSaver:
    def __init__(self, pg_conn):
        self.cursor = pg_conn.cursor()
        self.pg_conn = pg_conn
        self.db = None

    def save_all_data(self, data: dict):
        self.db = data
        # self.cursor.execute("""""")
        self.save_genres()
        self.save_persons()
        self.save_movies()
        self.save_movie_role()
        self.save_movie_genre()

    def save_genres(self):
        args = ','.join(
            self.cursor.mogrify("(%s, %s, current_timestamp, current_timestamp)",
                                (str(genre.id_pg), genre.name)).decode() for genre in self.db["genre"])
        self.cursor.execute(f"""
                        INSERT INTO content.genre (id, name, created, modified)
                        VALUES {args}
                        """)

    def save_persons(self):
        logger.info("save_person")
        args = ','.join(
            self.cursor.mogrify("(%s, %s, current_timestamp, current_timestamp)",
                                (str(actor.id_pg), actor.name)).decode() for actor in self.db["persons"])
        self.cursor.execute(f"""
                INSERT INTO content.person (id, full_name, created, modified)
                VALUES {args}
                """)
        logger.info("end_save_person")

    def save_movies(self):
        logger.info("start movies")
        args = ','.join(
            self.cursor.mogrify("(%s, %s, %s, %s, %s, current_timestamp, current_timestamp)", (
                str(film_work.id_pg), film_work.title, film_work.plot, None if film_work.imdb_rating == 'N/A' else film_work.imdb_rating,
                'b8e62e1f-4ac7-4bdd-8f02-cb415a4cf321')).decode() for film_work in self.db["movies"])
        self.cursor.execute(f"""
                                INSERT INTO content.film_work (id, title, description, rating, type_id, created, modified)
                                VALUES {args}
                                """)
        logger.info("end_movies")

    def save_movie_role(self):
        movie_person = []
        for movie in self.db["movies"]:
            for actor in movie.actor_list:
                id_id = str(uuid.uuid4())
                movie_person.append((id_id, str(movie.id_pg), str(actor), 'actor'))
                logger.info(id_id)
            for writer in movie.writer_list:
                movie_person.append((str(uuid.uuid4()), str(movie.id_pg), str(writer), 'writer'))
            for director in movie.director_list:
                movie_person.append((str(uuid.uuid4()), str(movie.id_pg), str(director), 'director'))
        args = ','.join(
            self.cursor.mogrify("(%s, %s, %s, %s, current_timestamp, current_timestamp)", item).decode() for
            item in movie_person)
        logger.info(f"")
        self.cursor.execute(f"""
                                        INSERT INTO content.person_film_role (id, film_id, person_id, role, created, modified)
                                        VALUES {args}
                                        """)

    def save_movie_genre(self):
        movie_genre = []
        for movie in self.db["movies"]:
            for genre in movie.genre_list:
                movie_genre.append((str(movie.id_pg), str(genre)))
        args = ','.join(
            self.cursor.mogrify("(%s, %s, current_timestamp, current_timestamp)", item).decode() for
            item in movie_genre)
        self.cursor.execute(f"""
                                                INSERT INTO content.film_work_genre (filmwork_id, genre_id, created, modified)
                                                VALUES {args}
                                                """)


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)

    data = sqlite_loader.load_movies()
    postgres_saver.save_all_data(data)


if __name__ == '__main__':
    dsl = {'dbname': 'movies_dev', 'user': 'movies', 'password': 'movies', 'host': 'movies-db', 'port': 5432}
    with sqlite3.connect('dumps_scripts/db.sqlite') as sqlite_conn, psycopg2.connect(**dsl,
                                                                                   cursor_factory=DictCursor) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
