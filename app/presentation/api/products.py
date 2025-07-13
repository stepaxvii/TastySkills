from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infrastructure.database.database import get_db
from app.presentation.api.auth import get_current_active_user
from app.domain.entities.models import User
from app.domain.entities.schemas import Product, ProductCreate
from app.infrastructure.repositories.crud import (
    create_product, get_product, get_products
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[Product])
def read_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Получение списка продуктов"""
    return get_products(db, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=Product)
def read_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Получение детальной информации о продукте"""
    product = get_product(db, product_id=product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.post("/", response_model=Product)
def create_new_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Создание нового продукта (только для staff)"""
    return create_product(db=db, product=product)


 