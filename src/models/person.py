from typing import List, Optional

import orjson
from pydantic import BaseModel, UUID4


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Person(BaseModel):
    id: UUID4
    full_name: str
    role: List[str]
    film_ids: Optional[List[UUID4]]

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
