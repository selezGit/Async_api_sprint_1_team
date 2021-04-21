from http import HTTPStatus
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, paginate
from pydantic import BaseModel
from services.film import FilmService, get_film_service

router = APIRouter()

class FilmShort(BaseModel):
    id: str
    title: str
    imdb_rating: Optional[float] = 0


# Внедряем FilmService с помощью Depends(get_film_service)
@router.get('/{film_id}', response_model=FilmShort)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> FilmShort:
    film = await film_service.get_by_id(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum
        # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='film not found')

    # Перекладываем данные из models.Film в Film
    # Обратите внимание, что у модели бизнес-логики есть поле description
        # Которое отсутствует в модели ответа API.
        # Если бы использовалась общая модель для бизнес-логики и формирования ответов API
        # вы бы предоставляли клиентам данные, которые им не нужны
        # и, возможно, данные, которые опасно возвращать
    return FilmShort(id=film.id, title=film.title, imdb_rating=film.rating)


@router.get('/film/search?query={query}', response_model=Page[FilmShort])
async def film_search(query: str, film_service: FilmService = Depends(get_film_service)):
    """Возвращает короткую информацию 
    по одному или нескольким фильмам"""

    films = await film_service.get_by_search(query)

    films_short: List = []
    for film in films:
        films_short.append(FilmShort(id=film.id, title=film.title, imdb_rating=film.rating))

    return paginate(films_short)
