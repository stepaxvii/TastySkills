from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.database.database import get_db
from app.presentation.api.auth import get_current_active_user, get_current_staff_user
from app.domain.entities.models import User
from app.domain.entities.schemas import Restaurant, RestaurantCreate, RestaurantWithRelations
from app.infrastructure.repositories.crud import (
    create_restaurant, get_restaurant, get_restaurants
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("/", response_model=List[Restaurant])
def read_restaurants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Получение списка ресторанов, доступных пользователю"""
    return get_restaurants(db, skip=skip, limit=limit)


@router.get("/{restaurant_id}", response_model=RestaurantWithRelations)
def read_restaurant(
    restaurant_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Получение детальной информации о ресторане"""
    restaurant = get_restaurant(db, restaurant_id=restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Возвращаем ресторан с отношениями
    return restaurant


@router.post("/", response_model=Restaurant)
def create_new_restaurant(
    restaurant: RestaurantCreate,
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
) -> Any:
    """Создание нового ресторана (только для staff)"""
    return create_restaurant(db=db, restaurant=restaurant) 