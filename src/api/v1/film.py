from enum import Enum
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from models.film import Film, FilmShort
from services.film import FilmService, get_film_service

router = APIRouter()


class Order(str, Enum):
    desc = 'DESC'
    asc = 'ASC'


@router.get("/", response_model=List[Film],
            summary='Получение списка фильмов с параметрами')
async def film_sort_filter(order: Optional[Order] = Order.desc,
                           genre: Optional[str] = None,
                           size: Optional[int] = 50,
                           page: Optional[int] = 1,
                           query: Optional[str] = None,
                           request: Request = None,
                           film_service: FilmService = Depends(
                               get_film_service)
                           ) -> Optional[List[FilmShort]]:
    """Возвращает короткую информацию по всем фильмам, отсортированным по рейтингу,
     есть возможность фильтровать фильмы по id жанров"""
    films = await film_service.get_by_param(request.url, order=order, genre=genre, page=page, size=size, query=query)

    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='film not found')

    return films


@router.get('/{film_id}', response_model=Film,
            summary='Фильм')
async def film_details(film_id: str,
                       request: Request = None,
                       film_service: FilmService = Depends(get_film_service)) -> Film:
    """Возвращает информацию по одному фильму"""
    film = await film_service.get_by_id(url=request.url, film_id=film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='film not found')
    return film
