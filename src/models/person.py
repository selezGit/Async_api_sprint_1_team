import uuid
from typing import List, Optional

import orjson
# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(v, default=default).decode()


class Person(BaseModel):
    id: uuid.UUID
    full_name: str
    role: str
    film_ids: Optional[List[uuid.UUID]]  # возможно тут будет косяк, проверить!

    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps
