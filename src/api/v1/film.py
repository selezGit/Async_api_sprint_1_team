from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from models.film import Film, FilmShort
from services.film import FilmService, get_film_service

router = APIRouter()


@router.get("/", response_model=List[Film])
async def film_sort_filter(sort: Optional[str] = '-rating',
                           genre: Optional[str] = None,
                           size: Optional[int] = 50,
                           page: Optional[int] = 1,
                           query: Optional[str] = None,
                           film_service: FilmService = Depends(
                               get_film_service)
                           ) -> Optional[List[FilmShort]]:
    """Возвращает короткую информацию по всем фильмам, отсортированным по рейтингу,
     есть возможность фильтровать фильмы по id жанров"""

    films = await film_service.get_by_param(sort=sort, genre=genre, page=page, size=size, query=query)

    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='film not found')

    return films


@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: str,
                       film_service: FilmService = Depends(get_film_service)) -> Film:
    """Возвращает информацию по одному фильму"""
    film = await film_service.get_by_id(film_id=film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='film not found')
    return film

