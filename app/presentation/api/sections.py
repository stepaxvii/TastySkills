from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.database.database import get_db
from app.presentation.api.auth import get_current_active_user
from app.domain.entities.models import User
from app.domain.entities.schemas import Section, SectionCreate, SectionWithRelations
from app.infrastructure.repositories.crud import (
    create_section, get_section, get_sections, get_sections_by_restaurant
)

router = APIRouter(prefix="/sections", tags=["sections"])


@router.get("/", response_model=List[Section])
def read_sections(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Получение списка разделов"""
    return get_sections(db, skip=skip, limit=limit)


@router.get("/restaurant/{restaurant_id}", response_model=List[Section])
def read_sections_by_restaurant(
    restaurant_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Получение списка разделов ресторана"""
    return get_sections_by_restaurant(db, restaurant_id)


@router.get("/{section_id}", response_model=SectionWithRelations)
def read_section(
    section_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Получение детальной информации о разделе"""
    section = get_section(db, section_id=section_id)
    if section is None:
        raise HTTPException(status_code=404, detail="Section not found")
    
    return section


@router.post("/", response_model=Section)
def create_new_section(
    section: SectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Создание нового раздела (только для staff)"""
    return create_section(db=db, section=section) 