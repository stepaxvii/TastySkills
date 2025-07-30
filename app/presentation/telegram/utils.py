"""
Утилиты для Telegram бота
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.repositories.crud import get_user_by_telegram_id, get_user_by_username
from app.presentation.telegram.keyboards import get_admin_menu_keyboard, get_manager_menu_keyboard, get_waiter_menu_keyboard
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "boba")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_db_session():
    """Контекстный менеджер для работы с базой данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_safely(db: Session, user_id: int, admin_username: str = ADMIN_USERNAME) -> Optional[object]:
    """
    Безопасное получение пользователя: сначала по telegram_id, затем по username
    """
    user = get_user_by_telegram_id(db, user_id)
    if not user:
        user = get_user_by_username(db, admin_username)
    return user


def is_admin_user(user) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user and (user.role == "admin" or user.username == ADMIN_USERNAME)


def is_manager_user(user) -> bool:
    """Проверка, является ли пользователь менеджером"""
    return user and user.role == "manager"


def is_waiter_user(user) -> bool:
    """Проверка, является ли пользователь официантом"""
    return user and user.role == "waiter"


async def send_welcome_message(message: Message, user, role: str) -> None:
    """Отправка приветственного сообщения с соответствующей клавиатурой"""
    role_emojis = {
        "admin": "👑",
        "manager": "👑", 
        "waiter": "👤"
    }
    
    role_names = {
        "admin": "Администратор",
        "manager": "Менеджер",
        "waiter": "Официант"
    }
    
    role_keyboards = {
        "admin": get_admin_menu_keyboard(),
        "manager": get_manager_menu_keyboard(),
        "waiter": get_waiter_menu_keyboard()
    }
    
    action_text = "управления" if role in ["admin", "manager"] else "работы"
    
    await message.answer(
        f"👋 Добро пожаловать, {user.telegram_first_name or user.username}!\n\n"
        f"{role_emojis[role]} Роль: {role_names[role]}\n"
        f"🔗 Веб-интерфейс: http://...\n\n"
        f"Используйте кнопки ниже для {action_text}:",
        reply_markup=role_keyboards[role]
    )


def create_copy_code_keyboard(invite_code: str, callback_prefix: str = "copy_invite_code") -> Optional[InlineKeyboardMarkup]:
    """Создание клавиатуры для копирования кода приглашения"""
    if not invite_code:
        return None
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Скопировать код", callback_data=f"{callback_prefix}:{invite_code}")]
        ]
    )


def extract_invite_code_from_link(link: str) -> Optional[str]:
    """Извлечение кода приглашения из ссылки"""
    if link and 'invite_' in link:
        return link.split('invite_')[-1]
    return None


def get_role_permission_message(role: str, action: str) -> str:
    """Получение сообщения об ошибке доступа для роли"""
    role_messages = {
        "admin": f"❌ Только администраторы могут {action}.",
        "manager": f"❌ Только менеджеры могут {action}.",
        "waiter": f"❌ Только официанты могут {action}."
    }
    return role_messages.get(role, f"❌ У вас нет прав для {action}.")


async def handle_database_error(message: Message, error: Exception, action: str) -> None:
    """Обработка ошибок базы данных"""
    logger.error(f"Ошибка при {action}: {error}")
    await message.answer(f"❌ Произошла ошибка при {action}. Попробуйте еще раз.") 