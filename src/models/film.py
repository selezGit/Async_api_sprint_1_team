import uuid
from datetime import datetime
from typing import List, Optional

import orjson
# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(v, default=default).decode()


class Person(BaseModel):
    id: uuid.UUID
    name: str


class Genre(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = ''


class Film(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = ''
    imdb_rating: Optional[float] = 0
    creation_date: datetime = datetime.now()
    restriction: Optional[int] = 0
    directors: List[Person] = []
    actors: List[Person] = []
    writers: List[Person] = []
    genres: List[Genre] = []
    file_path: Optional[str] = ''

    # type: str

    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class FilmShort(BaseModel):
    id: uuid.UUID
    title: str
    imdb_rating: Optional[float] = 0

    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps
