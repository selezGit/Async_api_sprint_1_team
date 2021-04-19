import orjson
import uuid
from typing import Optional, List
from datetime import datetime

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
    rating: Optional[float] = 0
    creation_date: datetime = datetime.now()
    restriction: Optional[int] = 0
    directors: List[Person]
    actors: List[Person]
    writers: List[Person]
    genre: List[Genre]
    file_link: Optional[str] = ''
    type: str


    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps




