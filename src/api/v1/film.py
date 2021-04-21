import uuid
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from models.film import Film
from pydantic import BaseModel
from services.film import FilmService, get_film_service

router = APIRouter()


class FilmShort(BaseModel):
    id: uuid.UUID
    title: str
    imdb_rating: Optional[float] = 0



@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    """Возвращает полную информацию по фильму
    """
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='film not found')
    return film


@router.get('/film/search?query={query}', response_model=FilmShort)
async def film_search(query: str, size: Optional[int] = 50,
                      page: Optional[int] = 1,
                      film_service: FilmService = Depends(get_film_service)
                      ) -> Optional[List[FilmShort]]:
    """Возвращает короткую информацию 
    по одному или нескольким фильмам"""

    films = await film_service.get_by_search(query, page, size)

    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='film not found')

    films_short = [FilmShort(id=film.id, title=film.title, imdb_rating=film.rating) for film in films]

    return films_short
