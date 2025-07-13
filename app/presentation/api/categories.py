from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.database.database import get_db
from app.presentation.api.auth import get_current_active_user
from app.domain.entities.models import User
from app.domain.entities.schemas import Category, CategoryCreate, CategoryWithRelations
from app.infrastructure.repositories.crud import (
    create_category, get_category, get_categories
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=List[Category])
def read_categories(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Получение списка категорий"""
    return get_categories(db, skip=skip, limit=limit)


@router.get("/{category_id}", response_model=CategoryWithRelations)
def read_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Получение детальной информации о категории"""
    category = get_category(db, category_id=category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


@router.post("/", response_model=Category)
def create_new_category(
    category: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Создание новой категории (только для staff)"""
    return create_category(db=db, category=category) 