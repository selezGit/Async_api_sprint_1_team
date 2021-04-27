import uuid
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.genre import GenreService, get_genre_service

router = APIRouter()


class Genre(BaseModel):
    id: uuid.UUID
    name: str


@router.get('/', response_model=List[Genre])
async def genre_all(size: Optional[int] = 50,
                    page: Optional[int] = 1,
                    genre_service: GenreService = Depends(get_genre_service)
                    ) -> Optional[List[Genre]]:
    """Возвращает инф-ию по всем жанрам с возможностью пагинации"""

    data = await genre_service.get_all(**{'page': page, 'size': size})
    if not data:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='genre not found')

    return data


@router.get('/{genre_id}', response_model=Genre)
async def genre_details(genre_id: str,
                        genre_service: GenreService = Depends(get_genre_service)) -> Genre:
    """Возвращает информацию по одному жанру"""
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='genre not found')
    return genre
