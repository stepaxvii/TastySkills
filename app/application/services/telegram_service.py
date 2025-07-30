import re
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.domain.entities.models import User, Invitation
from app.domain.entities.schemas import UserCreate
from app.infrastructure.repositories.crud import create_user, get_user_by_telegram_id, get_restaurants_by_manager


class TelegramService:
    """Сервис для работы с Telegram ботом"""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Валидация имени пользователя"""
        if not username:
            return False, "Логин не может быть пустым"
        if len(username) < 3:
            return False, "Логин должен содержать минимум 3 символа"
        if len(username) > 20:
            return False, "Логин должен содержать максимум 20 символов"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Логин может содержать только латинские буквы, цифры и знак подчеркивания"
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Валидация пароля"""
        if not password:
            return False, "Пароль не может быть пустым"
        if len(password) < 6:
            return False, "Пароль должен содержать минимум 6 символов"
        if len(password) > 50:
            return False, "Пароль должен содержать максимум 50 символов"
        return True, ""
    
    @staticmethod
    def create_manager_invitation_link(db: Session, manager: User, bot_username: str) -> str:
        """Создание постоянной ссылки приглашения для менеджера"""
        if manager.waiter_link:  # type: ignore
            return manager.waiter_link  # type: ignore
        
        # Генерируем постоянную ссылку для менеджера
        invitation_code = f"manager_{manager.id}_{secrets.token_urlsafe(6).upper()}"
        waiter_link = f"https://t.me/{bot_username}?start=invite_{invitation_code}"
        
        # Сохраняем ссылку в профиле менеджера
        manager.waiter_link = waiter_link  # type: ignore
        db.commit()
        
        return waiter_link
    
    @staticmethod
    def process_invitation_code(db: Session, invitation_code: str) -> Optional[dict]:
        """Обработка кода приглашения"""
        # Проверяем, является ли это постоянной ссылкой менеджера
        if invitation_code.startswith("manager_"):
            try:
                manager_id = int(invitation_code.split("_")[1])
                manager = db.query(User).filter(
                    User.id == manager_id,
                    User.role == "manager"
                ).first()
                
                waiter_link = getattr(manager, 'waiter_link', None)
                if manager and waiter_link and f"invite_{invitation_code}" in waiter_link:
                    return {
                        "type": "manager_link",
                        "manager_id": manager.id,
                        "manager_username": manager.username
                    }
            except (ValueError, IndexError):
                pass
        
        # Старая система приглашений (для обратной совместимости)
        invitation = db.query(Invitation).filter(
            Invitation.code == invitation_code,
            Invitation.is_used == False
        ).first()
        
        if invitation:
            return {
                "type": "invitation",
                "invitation_id": invitation.id,
                "manager_id": invitation.manager_id
            }
        
        return None
    
    @staticmethod
    def register_user(
        db: Session, 
        username: str, 
        password: str, 
        role: str, 
        telegram_data: dict,
        manager_id: Optional[int] = None,
        invitation_id: Optional[int] = None
    ) -> User:
        """Регистрация пользователя"""
        # Создаем пользователя
        user_create = UserCreate(
            username=username,
            password=password,
            role=role
        )
        
        user = create_user(db, user_create)
        
        # Устанавливаем Telegram данные
        user.telegram_id = telegram_data.get('id')  # type: ignore
        user.telegram_username = telegram_data.get('username')  # type: ignore
        user.telegram_first_name = telegram_data.get('first_name')  # type: ignore
        user.telegram_last_name = telegram_data.get('last_name')  # type: ignore
        user.is_telegram_user = True  # type: ignore
        
        # Если это официант, связываем с менеджером
        if role == "waiter" and manager_id:
            user.manager_id = manager_id  # type: ignore
            
            # Автоматически связываем официанта с рестораном менеджера
            TelegramService.link_waiter_to_manager_restaurant(db, user.id, manager_id)
            
            if invitation_id:
                invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
                if invitation:
                    invitation.is_used = True  # type: ignore
                    invitation.telegram_id = telegram_data.get('id')  # type: ignore
                    invitation.used_at = datetime.now(timezone.utc)  # type: ignore
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def link_waiter_to_manager_restaurant(db: Session, waiter_id: int, manager_id: int) -> None:
        """Связывание официанта с рестораном менеджера"""
        from app.domain.entities.models import Restaurant
        
        # Получаем ресторан менеджера
        manager_restaurants = get_restaurants_by_manager(db, manager_id)
        
        if manager_restaurants:
            # Берем первый ресторан менеджера
            restaurant = manager_restaurants[0]
            
            # Если у ресторана еще нет официанта, назначаем текущего
            if not restaurant.waiter_id:  # type: ignore
                restaurant.waiter_id = waiter_id  # type: ignore
                db.commit()
    
    @staticmethod
    def get_manager_waiters(db: Session, manager_id: int) -> list[User]:
        """Получение списка официантов менеджера"""
        return db.query(User).filter(User.manager_id == manager_id).all() 