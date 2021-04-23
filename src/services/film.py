from functools import lru_cache
from typing import Any, List, Optional

from aioredis import Redis
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, exceptions
from fastapi import Depends
from models.film import Film

from services.base import BaseService


class FilmService(BaseService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self,
                        film_id: str
                        ) -> Optional[Film]:
        """Функция получения фильма по id"""
        film = await self._check_cache(film_id, data_type='dict')
        if not film:
            film = await self._get_data_from_elastic(film_id)
            if not film:
                return None

            await self._load_cache(film_id, film)

        return film

    async def get_by_list_id(self,
                             person_id: str,
                             film_ids: List[str],
                             page: int,
                             size: int,
                             *args,
                             **kwargs
                             ) -> Optional[List[Film]]:
        """Функция получения фильмов по id"""

        filter = kwargs.get('filter')

        data = await self._check_cache(f'{person_id}:{filter}:{page}:{size}:list_ids')
        if not data:
            data = await self._get_data_from_elastic(film_ids, {'filter': filter, 'size': size, 'page': page})
            if not data:
                return None

            await self._load_cache(f'{person_id}:{filter}:{size}:{page}:list_ids', data)

        return data

    async def _get_data_from_elastic(self,
                                     data_id,
                                     *args,
                                     **kwargs
                                     ) -> Optional[List[Film]]:
        """Функция поиска объекта в elasticsearch по data_id или параметрам."""

        filter = kwargs.get('filter')
        size = kwargs.get('size')
        page = kwargs.get('page')

        if bool(bool(size)+bool(page)+bool(filter)):
            # если что то из этого есть,
            # значит запрос был сделан с параметрами
            if page:
                query = {'size': size, 'from': (page - 1) * size}

            if data_id:
                if data_id[0] == '-':
                    order = "DESC"
                    data_id = data_id[1:]
                else:
                    order = "ASC"

                query = {
                    "sort": {
                        data_id: {
                            "order": order
                        }
                    }
                }

                if filter:
                    query['query'] = {
                        "bool": {
                            "filter": {
                                "nested": {
                                    "path": "genres",
                                    "query": {
                                        "bool": {
                                            "must": {
                                                "match": {
                                                    "genres.id": filter
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

            try:
                doc = await self.elastic.search(index='movies', body=query)
            except exceptions.NotFoundError:
                print('index not found')
                return None

            if not doc:
                return None
            result = doc['hits']['hits']

            if not result:
                return None

            return [Film(**film['_source']) for film in result]

        else:
            # если параметров не было, значит ищем по id
            try:
                result = await self.elastic.get('movies', data_id)
                return Film(**result['_source'])

            except exceptions.NotFoundError:
                return None

    async def get_all_sorted(self,
                             sort: str,
                             page: int,
                             size: int) -> Optional[List[Film]]:
        """Функция получения всех фильмов в отсортированном виде"""

        films = await self._films_from_cache(sort, page, size)
        if not films:
            films = await self._get_all_sorted_from_elastic(sort, page, size)
            if not films:
                return None

            await self._put_films_to_cache(films, sort, page, size)

        return films

    async def get_by_search(self,
                            search: str,
                            page: int,
                            size: int
                            ) -> Optional[List[Film]]:
        """Функция поиска фильмов с параметрами"""
        films = await self._check_cache(f'{search}:{page}:{size}:search_film')
        if not films:
            films = await self._search_films_from_elastic(search, page, size)
            if not films:
                return None

            await self._load_cache(f'{search}:{page}:{size}:search_film', films)

        return films

    async def get_by_param(self,
                           sort: str,
                           filter: str,
                           page: int,
                           size: int
                           ) -> Optional[List[Film]]:
        """Функция получения всех фильмов с параметрами сортфировки\фильтрации"""
        films = await self._check_cache(f'{sort}:{filter}:{page}:{size}:key')

        if not films:

            films = await self._get_data_from_elastic(sort, {'filter': filter, 'page': page, 'size': size})
            if not films:
                return None

            await self._load_cache(f'{sort}:{filter}:{page}:{size}:key', films)

        return films

    async def _get_all_sorted_from_elastic(self,
                                           sort: str,
                                           page: int,
                                           size: int,
                                           *args,
                                           **kwargs
                                           ) -> Optional[List[Film]]:
        """функция получения фильмов в отсортированном порядке
        скорее всего это будет на ГЛАВНОЙ СТРАНИЦЕ"""

        if sort[0] == '-':
            order = "DESC"
            sort = sort[1:]
        else:
            order = "ASC"

        query = {
            'size': size,
            'from': (page - 1) * size,
            "sort": {
                sort: {
                    "order": order
                }
            }
        }

        genre_id = kwargs.get('filter')

        if genre_id:
            query['query'] = {
                "bool": {
                    "filter": {
                        "nested": {
                            "path": "genres",
                            "query": {
                                "bool": {
                                    "must": {
                                        "match": {
                                            "genres.id": genre_id
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

        doc = await self.elastic.search(index='movies', body=query)
        if not doc:
            return None
        result = doc['hits']['hits']

        if not result:
            return None

        return [Film(**film['_source']) for film in result]

    async def _search_films_from_elastic(self,
                                         search: str,
                                         page: int,
                                         size: int,
                                         ) -> Optional[List[Film]]:
        """Функция поиска фильмов по ключевому 
        слову, возвращает список найденных фильмов"""

        query = {
            'size': size,
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

        doc = await self.elastic.search(index='movies', body=query)
        if not doc:
            return None
        result = doc['hits']['hits']

        if not result:
            return None

        return [Film(**film['_source']) for film in result]

    async def _film_from_cache(self,
                               film_id: str
                               ) -> Optional[Film]:
        """Функция получения фильма по film_id."""
        data = await self.redis.get(film_id, )
        if not data:
            return None

        film = Film.parse_raw(data)
        return film

    async def _check_cache(self,
                           data_id: str,
                           data_type: Optional[str] = 'list'
                           ) -> Optional[Any]:
        """Найти обьекты в кэше."""

        if data_type == 'dict':
            # если запрос словаря, значит нужен поиск по id
            result = await self.redis.get(data_id, )
            return result
        else:
            # если несколько элементов, то поиск по списку
            result = await self.redis.lrange(data_id, 0, -1)
            if not result:
                return None

            data = [Film.parse_raw(film) for film in result]
            return data

    async def _load_cache(self,
                          data_id: str,
                          data: Any):
        """Запись объектов в кэш."""

        if isinstance(data, dict):
            await self.redis.set(data_id, data, ttl=self.FILM_CACHE_EXPIRE_IN_SECONDS)
        elif isinstance(data, list):
            await self.redis.lpush(data_id, [object.json() for object in data],
                                   expire=self.FILM_CACHE_EXPIRE_IN_SECONDS)
        else:
            print(f'failed load data: {data_id}')


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
