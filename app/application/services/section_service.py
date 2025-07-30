from app.domain.entities.schemas import SectionCreate, SectionUpdate
from app.infrastructure.repositories.crud import (
    get_section, create_section, update_section, delete_section, get_restaurant
)
from fastapi import HTTPException
from sqlalchemy.orm import Session

class SectionService:
    def __init__(self, db: Session):
        self.db = db

    def create_section(self, user, restaurant_id: int, data: SectionCreate):
        restaurant = get_restaurant(self.db, restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        section_data = data.model_copy(update={"restaurant_id": restaurant_id})
        return create_section(self.db, section_data)

    def update_section(self, user, section_id: int, data: SectionUpdate):
        section = get_section(self.db, section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        return update_section(self.db, section_id, data)

    def delete_section(self, user, section_id: int):
        section = get_section(self.db, section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        return delete_section(self.db, section_id) 