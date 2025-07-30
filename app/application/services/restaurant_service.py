from app.domain.entities.schemas import RestaurantCreate
from app.infrastructure.repositories.crud import (
    get_restaurant, create_restaurant, update_restaurant, delete_restaurant
)
from fastapi import HTTPException
from sqlalchemy.orm import Session

class RestaurantService:
    def __init__(self, db: Session):
        self.db = db

    def create_restaurant(self, user, data: RestaurantCreate):
        return create_restaurant(self.db, data)

    def update_restaurant(self, user, restaurant_id: int, data: dict):
        restaurant = get_restaurant(self.db, restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return update_restaurant(self.db, restaurant_id, data)

    def delete_restaurant(self, user, restaurant_id: int):
        restaurant = get_restaurant(self.db, restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return delete_restaurant(self.db, restaurant_id) 