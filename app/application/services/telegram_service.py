import re
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

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
    def create_admin_manager_invitation_link(db: Session, admin: User, bot_username: str) -> str:
        """Создание одноразовой ссылки приглашения для менеджера от админа"""
        # Генерируем одноразовую ссылку для менеджера
        invitation_code = f"admin_manager_{secrets.token_urlsafe(12).upper()}"
        manager_link = f"https://t.me/{bot_username}?start=invite_{invitation_code}"
        
        # Создаем запись приглашения
        invitation = Invitation(
            code=invitation_code,
            manager_id=admin.id,  # Админ как создатель приглашения
            is_used=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(invitation)
        db.commit()
        
        return manager_link
    
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
        
        # Проверяем, является ли это приглашением менеджера от админа
        if invitation_code.startswith("admin_manager_"):
            invitation = db.query(Invitation).filter(
                Invitation.code == invitation_code,
                Invitation.is_used == False
            ).first()
            
            if invitation:
                return {
                    "type": "admin_manager_invitation",
                    "invitation_id": invitation.id,
                    "admin_id": invitation.manager_id
                }
        
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
        
        # Если это менеджер по приглашению админа
        if role == "manager" and invitation_id:
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
    
    @staticmethod
    def get_admin_statistics(db: Session) -> Dict[str, Any]:
        """Получение статистики для администратора"""
        # Подсчет менеджеров
        managers_count = db.query(User).filter(User.role == "manager").count()
        
        # Подсчет официантов
        waiters_count = db.query(User).filter(User.role == "waiter").count()
        
        # Подсчет официантов по менеджерам
        waiters_by_manager = db.query(
            User.manager_id,
            func.count(User.id).label('waiters_count')
        ).filter(
            User.role == "waiter",
            User.manager_id.isnot(None)
        ).group_by(User.manager_id).all()
        
        # Детальная информация о менеджерах и их официантах
        managers_info = []
        for manager in db.query(User).filter(User.role == "manager").all():
            waiters = db.query(User).filter(
                User.manager_id == manager.id,
                User.role == "waiter"
            ).all()
            
            managers_info.append({
                "username": manager.username,
                "telegram_name": manager.telegram_first_name or "Не указано",
                "waiters_count": len(waiters),
                "created_at": manager.created_at.strftime('%d.%m.%Y') if manager.created_at else "Не указано"
            })
        
        return {
            "managers_count": managers_count,
            "waiters_count": waiters_count,
            "waiters_by_manager": waiters_by_manager,
            "managers_info": managers_info
        }
    
    @staticmethod
    def get_manager_statistics(db: Session, manager_id: int) -> Dict[str, Any]:
        """Получение статистики официантов для менеджера"""
        # Получаем всех официантов менеджера
        waiters = db.query(User).filter(
            User.manager_id == manager_id,
            User.role == "waiter"
        ).all()
        
        # Подсчет активных официантов
        active_waiters = [w for w in waiters if w.is_active]
        
        # Группировка по дате регистрации
        waiters_by_date = {}
        for waiter in waiters:
            date_str = waiter.created_at.strftime('%d.%m.%Y') if waiter.created_at else "Не указано"
            if date_str not in waiters_by_date:
                waiters_by_date[date_str] = 0
            waiters_by_date[date_str] += 1
        
        return {
            "total_waiters": len(waiters),
            "active_waiters": len(active_waiters),
            "inactive_waiters": len(waiters) - len(active_waiters),
            "waiters_by_date": waiters_by_date,
            "waiters_list": [
                {
                    "username": waiter.username,
                    "telegram_name": waiter.telegram_first_name or "Не указано",
                    "is_active": waiter.is_active,
                    "created_at": waiter.created_at.strftime('%d.%m.%Y') if waiter.created_at else "Не указано"
                }
                for waiter in waiters
            ]
        } 