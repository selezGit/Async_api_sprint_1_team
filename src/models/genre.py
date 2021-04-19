import orjson
import uuid
from typing import Optional

# Используем pydantic для упрощения работы при перегонке данных из json в объекты
from pydantic import BaseModel

def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(v, default=default).decode()

class Genre(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = ''
    rating: Optional[float] = 0.0