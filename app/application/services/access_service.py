from fastapi import HTTPException
from app.infrastructure.repositories.crud import get_restaurant, get_section, get_category, get_product
from app.domain.entities.models import User
from sqlalchemy.orm import Session
from typing import Optional

class AccessService:
    def __init__(self, db: Session):
        self.db = db

    def check_manager_access(self, user: Optional[User]):
        if not user or user.role not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Доступ запрещен. Требуются права менеджера.")

    def check_restaurant_access(self, user: Optional[User], restaurant_id: int):
        restaurant = get_restaurant(self.db, restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=404, detail="Ресторан не найден")
        # Здесь могут быть проверки на принадлежность ресторана пользователю

    def check_section_access(self, user: Optional[User], section_id: int):
        section = get_section(self.db, section_id)
        if not section:
            raise HTTPException(status_code=404, detail="Раздел не найден")
        self.check_restaurant_access(user, int(getattr(section, 'restaurant_id', -1)))

    def check_category_access(self, user: Optional[User], category_id: int):
        category = get_category(self.db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        self.check_restaurant_access(user, int(getattr(category, 'restaurant_id', -1)))

    def check_product_access(self, user: Optional[User], product_id: int):
        product = get_product(self.db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Продукт не найден")
        self.check_restaurant_access(user, int(getattr(product, 'restaurant_id', -1))) 