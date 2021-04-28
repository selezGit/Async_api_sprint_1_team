
import abc
import json
from typing import Any, Optional
import backoff


class BaseService:
    FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут

    @abc.abstractmethod
    async def get_by_id(self, *args, **kwargs) -> Any:
        """Получить объект по uuid"""
        pass

    @abc.abstractmethod
    async def get_all(self, *args, **kwargs) -> Any:
        """Получить все объекты в отсортированном виде"""
        pass

    @abc.abstractmethod
    async def _get_data_from_elastic(self, *args, **kwargs):
        """Функция поиска объекта в elasticsearch по data_id или параметрам."""
        pass

    @abc.abstractmethod
    async def get_by_search(self, *args, **kwargs) -> Any:
        """Найти объект(ы) по ключевому слову"""
        pass

    @abc.abstractmethod
    async def get_by_param(self, *args, **kwargs) -> Any:
        """Получить объекты по параметрам"""
        pass

    @backoff.on_exception(backoff.expo, Exception)
    async def _check_cache(self,
                           url: str,
                           ) -> Optional[Any]:

        """Найти обьекты в кэше."""
        result = await self.redis.get(str(url), )
        if result:
            result = json.loads(result)
        return result

    @backoff.on_exception(backoff.expo, Exception)
    async def _load_cache(self,
                          url: str,
                          data: Any):
        """Запись объектов в кэш."""
        data = json.dumps(data)
        await self.redis.set(key=str(url), value=data, expire=self.FILM_CACHE_EXPIRE_IN_SECONDS)
