from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="waiter")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    telegram_id = Column(Integer, unique=True, index=True, nullable=True)
    telegram_username = Column(String, nullable=True)
    telegram_first_name = Column(String, nullable=True)
    telegram_last_name = Column(String, nullable=True)
    is_telegram_user = Column(Boolean, default=False)
    
    waiter_link = Column(String, nullable=True)
    
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    managed_restaurants = relationship("Restaurant", foreign_keys="Restaurant.manager_id", back_populates="manager")
    waiter_restaurants = relationship("Restaurant", foreign_keys="Restaurant.waiter_id", back_populates="waiter")
    telegram_sessions = relationship("TelegramSession", back_populates="user")
    
    manager = relationship("User", foreign_keys=[manager_id], remote_side=[id])
    waiters = relationship("User", foreign_keys=[manager_id], overlaps="manager")

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    concept = Column(Text, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    waiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    manager = relationship("User", foreign_keys=[manager_id], back_populates="managed_restaurants")
    waiter = relationship("User", foreign_keys=[waiter_id], back_populates="waiter_restaurants")
    sections = relationship("Section", back_populates="restaurant")

class Section(Base):
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    restaurant = relationship("Restaurant", back_populates="sections")
    categories = relationship("Category", back_populates="section")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    section_id = Column(Integer, ForeignKey("sections.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    section = relationship("Section", back_populates="categories")
    restaurant = relationship("Restaurant")
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    weight = Column(String, nullable=True)
    ingredients = Column(Text)
    allergens = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    features = Column(Text, nullable=True)
    table_setting = Column(Text, nullable=True)
    gastronomic_pairings = Column(Text, nullable=True)
    image_path = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    modified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Boolean, default=False)
    
    category = relationship("Category", back_populates="products")
    restaurant = relationship("Restaurant")

class TelegramSession(Base):
    __tablename__ = "telegram_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    telegram_id = Column(Integer, index=True)
    state = Column(String, default="start")
    data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="telegram_sessions")

class Invitation(Base):
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    manager_id = Column(Integer, ForeignKey("users.id"))
    telegram_id = Column(Integer, nullable=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used_at = Column(DateTime, nullable=True)
    
    manager = relationship("User", foreign_keys=[manager_id]) 