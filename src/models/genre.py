from typing import Optional

import orjson
# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from pydantic import BaseModel, UUID4


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(v, default=default).decode()


class Genre(BaseModel):
    id: UUID4
    name: str
    description: Optional[str] = ''

    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps
