import logging
from functools import lru_cache
from typing import List, Optional

import backoff
from aioredis import Redis
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, exceptions
from fastapi import Depends
from models.film import Film
from models.person import Person

from services.base import BaseService


class PersonService(BaseService):
    def __init__(self,
                 redis: Redis,
                 elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self,
                        data_id: str,
                        *args,
                        **kwargs
                        ) -> Optional[Person]:
        """Получить объект по uuid"""
        key = f'person:{data_id}:key'
        data = await self._check_cache(key, )
        if not data:
            data = await self._get_data_from_elastic(data_id)
            if not data:
                return None

            await self._load_cache(key, data)

        return data

    async def get_all(self,
                      data_id: str,
                      *args,
                      **kwargs
                      ) -> Optional[List[Film]]:
        """Получить все объекты"""

        filter = kwargs.get('filter')
        size = kwargs.get('size')
        page = kwargs.get('page')
        key = f'persons:{data_id}:{filter}:{page}:{size}'
        data = await self._check_cache(key)
        if not data:
            data = await self._get_data_from_elastic(data_id, **{'filter': filter, 'size': size, 'page': page})
            if not data:
                return None

            await self._load_cache(key, data)

        return data

    async def get_by_search(self,
                            page: int,
                            size: int,
                            *args,
                            **kwargs
                            ) -> Optional[List[Person]]:
        """Найти объект(ы) по ключевому слову"""

        q = kwargs.get('q')
        key = f'persons:{q}:{page}:{size}'
        data = await self._check_cache(key)
        if not data:
            data = await self._get_data_from_elastic(page=page, size=size, q=q)
            if not data:
                return None
            await self._load_cache(key, data)

        return data

    @backoff.on_exception(backoff.expo, Exception)
    async def _get_data_from_elastic(self,
                                     data_id=None,
                                     *args,
                                     **kwargs
                                     ) -> Optional[List[Person]]:
        """Функция поиска объекта в elasticsearch по data_id или параметрам."""

        size = kwargs.get('size')
        page = kwargs.get('page')
        q = kwargs.get('q')

        if bool(bool(size) + bool(page)):
            # если что то из этого есть,
            # значит запрос был сделан с параметрами
            try:
                if page:
                    query = {
                        'size': size,
                        'from': (page - 1) * size,
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "match": {
                                            "full_name": q
                                        }
                                    }
                                ]
                            }
                        }
                    }
                doc = await self.elastic.search(index='persons', body=query)

            except exceptions.NotFoundError:
                logging.debug('index not found')
                return None

            if not doc:
                return None
            result = doc['hits']['hits']

            if not result:
                return None

            return [person['_source'] for person in result]

        else:
            # если параметров не было, значит ищем по id
            try:
                result = await self.elastic.get('persons', data_id)
                return result['_source']

            except exceptions.NotFoundError:
                return None


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
