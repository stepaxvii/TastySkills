from sqlalchemy.orm import Session
from app.domain.entities.models import User, Restaurant, Section, Category, Product, TelegramSession
from app.domain.entities.schemas import UserCreate, RestaurantCreate, SectionCreate, CategoryCreate, ProductCreate, TelegramUserCreate, TelegramSessionCreate
from app.presentation.api.auth import get_password_hash, verify_password
from typing import Optional, List, Dict, Any
import json

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_telegram_user(db: Session, user: TelegramUserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
        telegram_id=user.telegram_id,
        telegram_username=user.telegram_username,
        telegram_first_name=user.telegram_first_name,
        telegram_last_name=user.telegram_last_name,
        is_telegram_user=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: Any) -> Optional[User]:
    db_user = get_user(db, user_id)
    if db_user:
        for field, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[User]:
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def get_telegram_session(db: Session, telegram_id: int) -> Optional[TelegramSession]:
    return db.query(TelegramSession).filter(TelegramSession.telegram_id == telegram_id).first()

def create_telegram_session(db: Session, session: TelegramSessionCreate) -> TelegramSession:
    db_session = TelegramSession(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def update_telegram_session(db: Session, telegram_id: int, session_update: Any) -> Optional[TelegramSession]:
    db_session = get_telegram_session(db, telegram_id)
    if db_session:
        for field, value in session_update.dict(exclude_unset=True).items():
            setattr(db_session, field, value)
        db.commit()
        db.refresh(db_session)
    return db_session

def delete_telegram_session(db: Session, telegram_id: int) -> Optional[TelegramSession]:
    db_session = get_telegram_session(db, telegram_id)
    if db_session:
        db.delete(db_session)
        db.commit()
    return db_session

def set_session_data(db: Session, telegram_id: int, data: Dict[str, Any]) -> Optional[TelegramSession]:
    db_session = get_telegram_session(db, telegram_id)
    if db_session:
        db_session.data = json.dumps(data)  # type: ignore
        db.commit()
        db.refresh(db_session)
    return db_session

def get_session_data(db: Session, telegram_id: int) -> Dict[str, Any]:
    db_session = get_telegram_session(db, telegram_id)
    if db_session and db_session.data:  # type: ignore
        try:
            return json.loads(str(db_session.data))
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}

def get_restaurant(db: Session, restaurant_id: int) -> Optional[Restaurant]:
    return db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

def get_restaurants(db: Session, skip: int = 0, limit: int = 100) -> List[Restaurant]:
    return db.query(Restaurant).offset(skip).limit(limit).all()

def get_restaurants_by_manager(db: Session, manager_id: int) -> List[Restaurant]:
    return db.query(Restaurant).filter(Restaurant.manager_id == manager_id).all()

def get_restaurants_by_waiter(db: Session, waiter_id: int) -> List[Restaurant]:
    return db.query(Restaurant).filter(Restaurant.waiter_id == waiter_id).all()

def get_restaurants_by_waiter_via_manager(db: Session, waiter_id: int) -> List[Restaurant]:
    """Получение ресторанов официанта через его менеджера"""
    # Сначала получаем официанта
    waiter = db.query(User).filter(User.id == waiter_id).first()
    if not waiter or not waiter.manager_id:
        return []
    
    # Получаем рестораны менеджера
    return db.query(Restaurant).filter(Restaurant.manager_id == waiter.manager_id).all()

def create_restaurant(db: Session, restaurant: RestaurantCreate) -> Restaurant:
    db_restaurant = Restaurant(**restaurant.dict())
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

def update_restaurant(db: Session, restaurant_id: int, restaurant_update: Any) -> Optional[Restaurant]:
    db_restaurant = get_restaurant(db, restaurant_id)
    if db_restaurant:
        for field, value in restaurant_update.dict(exclude_unset=True).items():
            setattr(db_restaurant, field, value)
        db.commit()
        db.refresh(db_restaurant)
    return db_restaurant

def delete_restaurant(db: Session, restaurant_id: int) -> Optional[Restaurant]:
    db_restaurant = get_restaurant(db, restaurant_id)
    if db_restaurant:
        db.delete(db_restaurant)
        db.commit()
    return db_restaurant

def get_section(db: Session, section_id: int) -> Optional[Section]:
    return db.query(Section).filter(Section.id == section_id).first()

def get_sections(db: Session, skip: int = 0, limit: int = 100) -> List[Section]:
    return db.query(Section).offset(skip).limit(limit).all()

def get_sections_by_restaurant(db: Session, restaurant_id: int) -> List[Section]:
    return db.query(Section).filter(Section.restaurant_id == restaurant_id).all()

def create_section(db: Session, section: SectionCreate) -> Section:
    db_section = Section(**section.dict())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

def update_section(db: Session, section_id: int, section_update: Any) -> Optional[Section]:
    db_section = get_section(db, section_id)
    if db_section:
        for field, value in section_update.dict(exclude_unset=True).items():
            setattr(db_section, field, value)
        db.commit()
        db.refresh(db_section)
    return db_section

def delete_section(db: Session, section_id: int) -> Optional[Section]:
    db_section = get_section(db, section_id)
    if db_section:
        db.delete(db_section)
        db.commit()
    return db_section

def get_category(db: Session, category_id: int) -> Optional[Category]:
    return db.query(Category).filter(Category.id == category_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
    return db.query(Category).offset(skip).limit(limit).all()

def get_categories_by_section(db: Session, section_id: int) -> List[Category]:
    return db.query(Category).filter(Category.section_id == section_id).all()

def get_categories_by_restaurant(db: Session, restaurant_id: int) -> List[Category]:
    return db.query(Category).filter(Category.restaurant_id == restaurant_id).all()

def create_category(db: Session, category: CategoryCreate) -> Category:
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, category_update: Any) -> Optional[Category]:
    db_category = get_category(db, category_id)
    if db_category:
        for field, value in category_update.dict(exclude_unset=True).items():
            setattr(db_category, field, value)
        db.commit()
        db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int) -> Optional[Category]:
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category

def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    return db.query(Product).offset(skip).limit(limit).all()

def get_products_by_category(db: Session, category_id: int) -> List[Product]:
    return db.query(Product).filter(Product.category_id == category_id).all()

def get_products_by_restaurant(db: Session, restaurant_id: int) -> List[Product]:
    return db.query(Product).filter(Product.restaurant_id == restaurant_id).all()

def get_recent_products(db: Session, limit: int = 10) -> List[Product]:
    return db.query(Product).order_by(Product.modified_at.desc()).limit(limit).all()

def get_recent_products_by_restaurants(db: Session, restaurant_ids: List[int], limit: int = 10) -> List[Product]:
    return db.query(Product).filter(Product.restaurant_id.in_(restaurant_ids)).order_by(Product.modified_at.desc()).limit(limit).all()

def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: Any) -> Optional[Product]:
    db_product = get_product(db, product_id)
    if db_product:
        for field, value in product_update.dict(exclude_unset=True).items():
            setattr(db_product, field, value)
        db.commit()
        db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int) -> Optional[Product]:
    db_product = get_product(db, product_id)
    if db_product:
        db_product.is_deleted = True # type: ignore
        db.commit()
        db.refresh(db_product)
    return db_product

def get_first_product_by_category(db: Session, category_id: int):
    return db.query(Product).filter(Product.category_id == category_id).order_by(Product.id.asc()).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):  # type: ignore
        return None
    return user

def authenticate_telegram_user(db: Session, telegram_id: int) -> Optional[User]:
    return get_user_by_telegram_id(db, telegram_id) 