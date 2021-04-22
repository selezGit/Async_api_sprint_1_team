
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from models.person import Person
from pydantic import BaseModel
from services.person import PersonService, get_person_service

router = APIRouter()


@router.get('/{person_id}', response_model=Person)
async def person_details(person_id: str,
                         person_service: PersonService = Depends(get_person_service)
                         ) -> Person:
    """Возвращает информацию по одной персоне"""
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='person not found')
    return person


@router.get('/search?query={query}', response_model=Person)
async def person_search(query: str,
                        size: Optional[int] = 50,
                        page: Optional[int] = 1,
                        person_service: PersonService = Depends(
                            get_person_service)
                        ) -> Optional[List[Person]]:
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
