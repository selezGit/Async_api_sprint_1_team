from functools import lru_cache
from typing import Optional, List

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, exceptions
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from uuid import UUID

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str
                        ) -> Optional[Film]:
        """Функция получения фильма по id"""
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None

            await self._put_film_to_cache(film)

        return film

    async def _get_film_from_elastic(self, film_id: str
                                     ) -> Optional[Film]:
        """Функция поиска фильма в elasticsearch по film_id."""
        try:
            doc = await self.elastic.get('movies', film_id)
            return Film(**doc['_source'])

        except exceptions.NotFoundError:
            return None

    async def get_by_search(self, search: str,
                            page: int,
                            size: int
                            ) -> Optional[List[Film]]:
        """Функция получения фильмов путём поиска с параметрами"""
        films = await self._films_from_cache(search, page, size)
        if not films:
            films = await self._search_films_from_elastic(search, page, size)
            if not films:
                return None

            await self._put_films_to_cache(films, search, page, size)

        return films

    async def _search_films_from_elastic(self,
                                         search: str,
                                         page: int,
                                         size: int,
                                         ) -> Optional[List[Film]]:
        """Функция поиска фильмов по ключевому 
        слову, возвращает список найденных фильмов"""

        query = {
            'limit': size,
            'from': (page - 1) * size,
            "query": {
                "bool": {
                    "must": {
                        "multi_match": {
                            "type": "best_fields",
                            "query": search,
                            "fuzziness": "auto",
                            "fields": [
                                    "title^5",
                                    "description^4",
                                    "genres_names^3",
                                    "actors_names^3",
                                    "writers_names^2",
                                    "directors_names^1"
                            ]
                        }
                    }
                }
            }
        }

        try:
            doc = await self.elastic.search(index='movies', body=query)
            return [Film(**film['_source']) for film in doc]

        except exceptions.NotFoundError:
            return None

    async def _film_from_cache(self, film_id: str
                               ) -> Optional[Film]:
        """Функция получения фильма по film_id."""
        data = await self.redis.get(film_id, )
        if not data:
            return None

        film = Film.parse_raw(data)
        return film

    async def _films_from_cache(self, search: str,
                                page: int,
                                size: int
                                ) -> Optional[List[Film]]:
        """Функция получения списка фильмов по параметрам."""
        data = await self.redis.lrange(f'{search}:{page}:{size}:key', 0, -1, encoding='utf-8')
        if not data:
            return None

        films = [Film.parse_raw(film) for film in data]
        return films

    async def _put_film_to_cache(self, film: Film
                                 ) -> None:
        """Сохраняем данные о фильме в redis"""
        await self.redis.set(film.id, film.json(), expire=FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _put_films_to_cache(self, films: List[Film],
                                  search: str,
                                  page: int,
                                  size: int
                                  ) -> None:
        """Сохраняем список фильмов в redis"""
        await self.redis.lpush(f'{search}:{page}:{size}:key',
                               [film.json() for film in films],
                               expire=FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
