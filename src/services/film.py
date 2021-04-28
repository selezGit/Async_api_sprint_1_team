import logging
from functools import lru_cache
from typing import Dict, List, Optional

import backoff
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
                        url: str,
                        film_id: str
                        ) -> Optional[Dict]:
        """Функция получения фильма по id"""
        film = await self._check_cache(url)
        if not film:
            film = await self._get_data_from_elastic(data_id=film_id)
            if not film:
                return None

            await self._load_cache(url, film)

        return film

    async def get_by_list_id(self,
                             url: str,
                             person_id: str,
                             film_ids: List[str],
                             page: int,
                             size: int,
                             *args,
                             **kwargs
                             ) -> Optional[List[Dict]]:
        """Функция получения фильмов по id"""

        data = await self._check_cache(url)
        if not data:
            data = await self._get_data_with_list_film(film_ids=film_ids, page=page, size=size)
            if not data:
                return None

            await self._load_cache(url, data)

        return data

    @backoff.on_exception(backoff.expo, Exception)
    async def _get_data_with_list_film(self, film_ids: List[str], page: int, size: int):
        query = {
            "size": size,
            "from": (page - 1) * size,
            "query": {
                "bool": {
                    "should": [
                        {
                            "match_phrase": {
                                "id": film_id
                            }
                        } for film_id in film_ids
                    ],
                    "minimum_should_match": 1
                }
            }
        }

        try:
            doc = await self.elastic.search(index='movies', body=query)
        except exceptions.NotFoundError:
            logging.error('index not found')
            return None

        if not doc:
            return None
        result = doc['hits']['hits']

        if not result:
            return None
        return [film['_source'] for film in result]

    @backoff.on_exception(backoff.expo, Exception)
    async def _get_data_from_elastic(self,
                                     data_id: Optional[str] = None,
                                     *args,
                                     **kwargs
                                     ) -> Optional[List[Film]]:
        """Функция поиска объекта в elasticsearch по data_id или параметрам."""

        genre = kwargs.get('genre')
        size = kwargs.get('size')
        page = kwargs.get('page')
        order = kwargs.get('order')
        q = kwargs.get('query')

        if any([size, page, genre, order, q]):
            # если что то из этого есть,
            # значит запрос был сделан с параметрами

            query = {'size': size, 'from': (page - 1) * size}

            if order:

                query['sort'] = {
                    "imdb_rating": {
                        "order": order
                    }
                }

            if genre:
                query['query'] = {
                    "bool": {
                        "filter": {
                            "bool": {
                                "should": {
                                    "match_phrase": {
                                        "genres.id": genre
                                    }
                                }
                            }
                        }
                    }
                }

            if q:
                _query = query.setdefault("query", dict())
                _bool = _query.setdefault("bool", dict())
                _bool['must'] = {
                    "multi_match": {
                        "type": "best_fields",
                        "query": q,
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
                _query['bool'] = _bool
                query['query'] = _query

            try:
                logging.info(query)
                doc = await self.elastic.search(index='movies', body=query)
            except exceptions.NotFoundError:
                logging.error('index not found')
                return None

            if not doc:
                return None
            result = doc['hits']['hits']

            if not result:
                return None

            return [film['_source'] for film in result]

        else:
            # если параметров не было, значит ищем по id
            try:
                result = await self.elastic.get('movies', data_id)
                return result['_source']

            except exceptions.NotFoundError:
                return None

    async def get_by_param(self,
                           url: str,
                           order: str,
                           page: int,
                           size: int,
                           genre: str = None,
                           query: str = None
                           ) -> Optional[List[Film]]:
        """Функция получения всех фильмов с параметрами сортфировки и фильтрации"""
        films = await self._check_cache(url)
        if not films:

            films = await self._get_data_from_elastic(
                **{'genre': genre, 'page': page, 'size': size, 'order': order, 'query': query})
            if not films:
                return None

            await self._load_cache(url, films)

        return films


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
