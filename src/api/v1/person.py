
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from models.person import Person
from pydantic import BaseModel
from services.person import PersonService, get_person_service

router = APIRouter()



@router.get('/{person_id}', response_model=Person)
async def person_details(person_id: str,
                       person_service: PersonService = Depends(get_person_service)) -> Person:
    """Возвращает информацию по одной персоне"""
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='person not found')
    return person