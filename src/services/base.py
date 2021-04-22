
import abc
from typing import Any


class BaseService:
    @abc.abstractmethod
    async def get_by_id(self, *args, **kwargs) -> Any:
        """Получить объект по uuid"""
        pass

    @abc.abstractmethod
    async def get_all(self, *args, **kwargs) -> Any:
        """Получить все объекты в отсортированном виде"""
        pass

    @abc.abstractmethod
    async def get_by_search(self, *args, **kwargs) -> Any:
        """Найти объект по ключевому слову"""
        pass

    @abc.abstractmethod
    async def get_by_param(self, *args, **kwargs) -> Any:
        """Получить объекты по параметрам"""
        pass

    @abc.abstractmethod
    async def _check_cache(self, *args, **kwargs) -> Any:
        """Поискать объект\ы в кеше"""
        pass

    @abc.abstractmethod
    async def _load_cache(self, *args, **kwargs) -> None:
        """Записать объект\ы в кэш"""
        pass
