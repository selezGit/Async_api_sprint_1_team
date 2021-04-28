import logging
from functools import lru_cache
from typing import Dict, List, Optional

import backoff
from aioredis import Redis
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, exceptions
from fastapi import Depends
from models.genre import Genre

from services.base import BaseService


class GenreService(BaseService):
    def __init__(self,
                 redis: Redis,
                 elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self,
                        url: str,
                        data_id: str,
                        *args,
                        **kwargs
                        ) -> Optional[Genre]:
        """Получить объект по uuid"""
        data = await self._check_cache(url)
        print(data)
        print(url)
        if not data:
            data = await self._get_data_from_elastic(data_id)
            if not data:
                return None

            await self._load_cache(url, data)

        return data

    async def get_all(self,
                      url: str,
                      *args,
                      **kwargs
                      ) -> Optional[List[Genre]]:
        """Получить все объекты"""

        filter = kwargs.get('filter')
        size = kwargs.get('size')
        page = kwargs.get('page')
        data = await self._check_cache(url)
        if not data:
            data = await self._get_data_from_elastic(**{'filter': filter, 'size': size, 'page': page})
            if not data:
                return None

            await self._load_cache(url, data)

        return data

    @backoff.on_exception(backoff.expo, Exception)
    async def _get_data_from_elastic(self,
                                     data_id=None,
                                     *args,
                                     **kwargs
                                     ) -> Optional[List[Dict]]:
        """Функция поиска объекта в elasticsearch по data_id или параметрам."""

        size = kwargs.get('size')
        page = kwargs.get('page')

        if bool(bool(size) + bool(page)):

            # если что то из этого есть,
            # значит запрос был сделан с параметрами
            try:
                if page:
                    query = {'size': size, 'from': (page - 1) * size}
                doc = await self.elastic.search(index='genre', body=query)
            except exceptions.NotFoundError:
                logging.info('index not found')
                return None

            if not doc:
                return None
            result = doc['hits']['hits']

            if not result:
                return None

            return [genre['_source'] for genre in result]

        else:
            # если параметров не было, значит ищем по id
            try:
                result = await self.elastic.get('genre', data_id)
                return result['_source']

            except exceptions.NotFoundError:
                return None


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
