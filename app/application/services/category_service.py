from app.domain.entities.schemas import CategoryCreate, CategoryUpdate
from app.infrastructure.repositories.crud import (
    get_category, create_category, update_category, delete_category, get_section
)
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, user, section_id: int, data: CategoryCreate):
        section = get_section(self.db, section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        category_data = data.model_copy(update={"section_id": section_id, "restaurant_id": section.restaurant_id})
        return create_category(self.db, category_data)

    def update_category(self, user, category_id: int, data: CategoryUpdate):
        category = get_category(self.db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return update_category(self.db, category_id, data)

    def delete_category(self, user, category_id: int):
        category = get_category(self.db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return delete_category(self.db, category_id) 