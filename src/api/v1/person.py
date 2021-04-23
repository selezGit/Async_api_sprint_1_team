import uuid
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from models.person import Person
from pydantic import BaseModel
from services.film import FilmService, get_film_service
from services.person import PersonService, get_person_service

router = APIRouter()


class FilmShort(BaseModel):
    id: uuid.UUID
    title: str
    rating: Optional[float] = 0


@router.get('/{person_id}', response_model=Person)
async def person_details(person_id: str,
                         person_service: PersonService = Depends(
                             get_person_service)
                         ) -> Person:
    """Возвращает информацию по одной персоне"""
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='person not found')
    return person


@router.get('/{person_id}/films', response_model=Person)
async def films_with_person(person_id: str,
                            size: Optional[int] = 50,
                            page: Optional[int] = 1,
                            person_service: PersonService = Depends(
                                get_person_service),
                            film_service: FilmService = Depends(
                                get_film_service)
                            ) -> List[FilmShort]:
    """Возвращает информацию по одной персоне"""
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='person not found')

    films = await film_service.get_by_list_id(person.id, person.ids, page, size)

    return person


@router.get('/search?query={query}', response_model=Person)
async def person_search(query: str,
                        size: Optional[int] = 50,
                        page: Optional[int] = 1,
                        person_service: PersonService = Depends(
                            get_person_service)
                        ) -> List[Person]:
    """Возвращает информацию 
    по одному или нескольким персонам"""

    persons = await person_service.get_by_search(query, page, size)

    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='person not found')

    persons = [Person(id=person.id,
                      full_name=person.full_name,
                      role=person.role,
                      film_ids=person.film_ids,
                      rating=person.rating) for person in persons]

    return persons
