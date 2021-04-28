from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from models.person import Person
from models.film import FilmShort
from services.film import FilmService, get_film_service
from services.person import PersonService, get_person_service

router = APIRouter()


@router.get('/{person_id}', response_model=Person,
            summary='Персона')
async def person_details(person_id: str,
                         request: Request = None,
                         person_service: PersonService = Depends(
                             get_person_service)
                         ) -> Person:
    """Возвращает информацию по одной персоне"""
    person = await person_service.get_by_id(request.url, person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='person not found')
    return person


@router.get('/{person_id}/films', response_model=List[FilmShort],
            summary='Фильмы с участием персоны')
async def films_with_person(person_id: str,
                            size: Optional[int] = 50,
                            page: Optional[int] = 1,
                            request: Request = None,
                            person_service: PersonService = Depends(
                                get_person_service),
                            film_service: FilmService = Depends(
                                get_film_service)
                            ) -> List[FilmShort]:
    """Возвращает список фильмов в которых участвовал персонаж"""
    # отсекаем окончание запроса для получения валидного кэша
    person_url = '/'.join(str(request.url).split('/')[:-1])
    person = await person_service.get_by_id(person_url, person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='person not found')

    films = await film_service.get_by_list_id(url=request.url,
                                              person_id=person['id'],
                                              film_ids=person['film_ids'],
                                              page=page, size=size)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='film not found')

    return films


@router.get('/', response_model=List[Person],
            summary='Список персон')
async def person_search(query: Optional[str] = None,
                        size: Optional[int] = 50,
                        page: Optional[int] = 1,
                        request: Request = None,
                        person_service: PersonService = Depends(
                            get_person_service)
                        ) -> List[Person]:
    """Возвращает информацию
    по одному или нескольким персонам"""

    persons = await person_service.get_by_param(url=request.url, q=query, page=page, size=size)

    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='person not found')

    return persons
