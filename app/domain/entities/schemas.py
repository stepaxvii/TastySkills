from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    role: str = "waiter"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_first_name: Optional[str] = None
    telegram_last_name: Optional[str] = None
    is_telegram_user: bool = False

    class Config:
        from_attributes = True

class TelegramUserCreate(BaseModel):
    telegram_id: int
    telegram_username: Optional[str] = None
    telegram_first_name: Optional[str] = None
    telegram_last_name: Optional[str] = None
    username: str
    password: str
    role: str = "waiter"

class TelegramSessionCreate(BaseModel):
    telegram_id: int
    state: str = "start"
    data: Optional[str] = None

class TelegramSessionUpdate(BaseModel):
    state: Optional[str] = None
    data: Optional[str] = None

class TelegramSession(BaseModel):
    id: int
    user_id: Optional[int] = None
    telegram_id: int
    state: str
    data: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RestaurantBase(BaseModel):
    name: str
    concept: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    manager_id: Optional[int] = None
    waiter_id: Optional[int] = None

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    concept: Optional[str] = None
    manager_id: Optional[int] = None
    waiter_id: Optional[int] = None

class Restaurant(RestaurantBase):
    id: int
    manager_id: Optional[int] = None
    waiter_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SectionBase(BaseModel):
    name: str
    description: Optional[str] = None

class SectionCreate(SectionBase):
    restaurant_id: int

class SectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    restaurant_id: Optional[int] = None

class Section(SectionBase):
    id: int
    restaurant_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    title: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    section_id: int
    restaurant_id: int

class CategoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    section_id: Optional[int] = None
    restaurant_id: Optional[int] = None

class Category(CategoryBase):
    id: int
    section_id: int
    restaurant_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    title: str
    weight: Optional[str] = None
    ingredients: str
    allergens: Optional[str] = None
    description: Optional[str] = None
    features: Optional[str] = None
    table_setting: Optional[str] = None
    gastronomic_pairings: Optional[str] = None
    image_path: Optional[str] = None
    is_deleted: Optional[bool] = False

class ProductCreate(ProductBase):
    category_id: int
    restaurant_id: int

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    weight: Optional[str] = None
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
    description: Optional[str] = None
    features: Optional[str] = None
    table_setting: Optional[str] = None
    gastronomic_pairings: Optional[str] = None
    image_path: Optional[str] = None
    category_id: Optional[int] = None
    restaurant_id: Optional[int] = None

class Product(ProductBase):
    id: int
    category_id: int
    restaurant_id: int
    created_at: datetime
    modified_at: datetime
    is_deleted: bool = False

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Message(BaseModel):
    message: str

class RestaurantWithRelations(Restaurant):
    sections: List['Section'] = []
    manager: Optional[User] = None
    waiter: Optional[User] = None

class SectionWithRelations(Section):
    categories: List['Category'] = []
    restaurant: Restaurant

class CategoryWithRelations(Category):
    products: List[Product] = []
    section: Section
    restaurant: Restaurant 