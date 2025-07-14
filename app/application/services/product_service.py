from app.domain.entities.schemas import ProductCreate, ProductUpdate
from app.infrastructure.repositories.crud import (
    get_product, create_product, update_product, delete_product, get_category
)
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def create_product(self, user, category_id: int, data: ProductCreate, image_path: Optional[str] = None):
        category = get_category(self.db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        product_data = data.model_copy(update={"image_path": image_path, "category_id": category_id, "restaurant_id": category.restaurant_id})
        return create_product(self.db, product_data)

    def update_product(self, user, product_id: int, data: ProductUpdate, image_path: Optional[str] = None):
        product = get_product(self.db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        update_data = data.model_copy(update={"image_path": image_path} if image_path else {})
        return update_product(self.db, product_id, update_data)

    def delete_product(self, user, product_id: int):
        product = get_product(self.db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return delete_product(self.db, product_id) 