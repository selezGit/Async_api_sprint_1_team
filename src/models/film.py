import uuid
from datetime import datetime
from typing import List, Optional

import orjson
from pydantic import BaseModel

from models.genre import Genre


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Person(BaseModel):
    id: uuid.UUID
    name: str


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

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class FilmShort(BaseModel):
    id: uuid.UUID
    title: str
    imdb_rating: Optional[float] = 0

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
