from functools import lru_cache
from typing import Any, List, Optional

from aioredis import Redis
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, exceptions
from fastapi import Depends
from models.genre import Genre

from services.base import BaseService

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService(BaseService):

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, data_id: str, *args, **kwargs) -> Optional[Genre]:
        """Получить объект по uuid"""

        data = await self._check_cache(data_id, data_type='dict')
        if not data:
            data = await self._get_data_from_elastic(data_id)  # TODO
            if not data:
                return None

            await self._load_cache(data_id, data)

        return data

    async def get_all(self, category: str, *args, **kwargs) -> Optional[List[Genre]]:
        """Получить все объекты"""

        filter = kwargs.get('filter')
        size = kwargs.get('size')
        page = kwargs.get('page')

        data = await self._check_cache(f'{category}:{filter}:{page}:{size}:key')
        if not data:
            # TODO
            data = await self._get_data_from_elastic(category, {'filter': filter, 'size': size, 'page': page})
            if not data:
                return None

            await self._load_cache(f'{category}:{filter}:{size}:{page}:key', data)

        return data

    async def _get_data_from_elastic(self,
                                     data_id,
                                     *args,
                                     **kwargs
                                     ) -> Optional[List[Genre]]:
        """Функция поиска фильма в elasticsearch по film_id или параметрам."""

        filter = kwargs.get('filter')
        size = kwargs.get('size', 50)
        page = kwargs.get('page', 1)

        if bool(bool(filter)+bool(size)+bool(page)):
            # если что то из этого есть,
            # значит запрос был сделан с параметрами
            query = await self._es_sort_query(data_id, page, size, {'filter': filter})

            doc = await self.elastic.search(index='movies', body=query)
            if not doc:
                return None
            result = doc['hits']['hits']

            if not result:
                return None

            return [Genre(**film['_source']) for film in result]

        else:
            # если параметров не было, значит ищем по id
            try:
                doc = await self.elastic.get('movies', data_id)
                return Genre(**doc['_source'])

            except exceptions.NotFoundError:
                return None

    async def _check_cache(self,
                           data_id: str,
                           data_type: Optional[str] = 'list'
                           ) -> Optional[Any]:
        """Найти данные в кэше."""

        if data_type == 'dict':
            # если запрос словаря, значит нужен поиск по id
            result = await self.redis.get(data_id)
            return result
        else:
            # если несколько элементов, то поиск по списку
            result = await self.redis.lrange(data_id, 0, -1)
            if not result:
                return None

            data = [Genre.parse_raw(genre) for genre in result]
            return data

    async def _load_cache(self, data_id: str, data: Any):
        """Загрузка данных в кэш."""

        if isinstance(data, dict):
            await self.redis.set(data_id, data, ttl=FILM_CACHE_EXPIRE_IN_SECONDS)
        elif isinstance(data, list):
            await self.redis.lpush(data_id, [object.json() for object in data],
                                   expire=FILM_CACHE_EXPIRE_IN_SECONDS)
        else:
            print(f'failed load data: {data_id}')

    async def _es_sort_query(self,
                             data_id: str,
                             page: int,
                             size: int,
                             *args,
                             **kwargs
                             ) -> Optional[dict]:

        if data_id[0] == '-':
            order = "DESC"
            data_id = data_id[1:]
        else:
            order = "ASC"

        query = {
            'size': size,
            'from': (page - 1) * size,
            "sort": {
                data_id: {
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

        return query


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
