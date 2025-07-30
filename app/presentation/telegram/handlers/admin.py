from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.infrastructure.database.database import SessionLocal
from app.infrastructure.repositories.crud import get_user_by_telegram_id, get_user_by_username
from app.application.services.telegram_service import TelegramService
from app.presentation.telegram.keyboards import get_admin_menu_keyboard
from aiogram.types import CallbackQuery
import os
import logging
from dotenv import load_dotenv

load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "boba")
logger = logging.getLogger(__name__)

admin_router = Router()

def is_admin_user(user) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user and (user.role == "admin" or user.username == ADMIN_USERNAME)

@admin_router.message(F.text == "👑 Пригласить менеджера")
async def create_manager_invitation(message: Message, bot: Bot) -> None:
    """Создание приглашения для менеджера от админа"""
    assert message.from_user is not None
    user_id = message.from_user.id
    db = SessionLocal()
    try:
        # Сначала ищем по telegram_id, затем по username
        user = get_user_by_telegram_id(db, user_id)
        logger.info(f"Поиск пользователя по telegram_id {user_id}: {user}")
        
        if not user:
            user = get_user_by_username(db, ADMIN_USERNAME)
            logger.info(f"Поиск пользователя по username {ADMIN_USERNAME}: {user}")
        
        logger.info(f"Проверка админа: user={user}, is_admin={is_admin_user(user)}")
        
        if not is_admin_user(user):
            await message.answer("❌ Только администраторы могут создавать приглашения для менеджеров.")
            return
        
        bot_username = (await bot.get_me()).username or ""
        manager_link = TelegramService.create_admin_manager_invitation_link(db, user, bot_username)
        
        # Извлечь код приглашения из ссылки
        invite_code = None
        if manager_link and 'invite_' in manager_link:
            invite_code = manager_link.split('invite_')[-1]
        
        # Клавиатура для копирования кода
        copy_code_kb = None
        if invite_code:
            copy_code_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Скопировать код", callback_data=f"copy_manager_code:{invite_code}")]
                ]
            )
        
        await message.answer(
            f"👑 Приглашение менеджера в TastySkills:\n\n"
            f"🔗 {manager_link}\n"
            + (f"Код для регистрации: {invite_code}\n" if invite_code else ""),
            reply_markup=copy_code_kb
        )
        await message.answer(
            "Перешлите сообщение с ссылкой человеку, которого хотите назначить менеджером в TastySkills.\n"
            "⚠️ Ссылка одноразовая и будет использована при регистрации."
        )
    except Exception as e:
        logger.error(f"Ошибка при создании приглашения менеджера: {e}")
        await message.answer("❌ Произошла ошибка при создании пригласительной ссылки.")
    finally:
        db.close()

@admin_router.callback_query(F.data.startswith("copy_manager_code:"))
async def copy_manager_code_callback(callback: CallbackQuery):
    """Обработчик для копирования кода приглашения менеджера"""
    if not callback.data:
        await callback.answer("Нет кода для копирования.", show_alert=True)
        return
    code = callback.data.split(":", 1)[-1]
    if not callback.message:
        await callback.answer("Нет сообщения для отправки кода.", show_alert=True)
        return
    await callback.answer("Код скопирован!", show_alert=False)
    await callback.message.answer(f"Код для регистрации менеджера: {code}")

@admin_router.message(F.text == "📊 Статистика")
async def show_admin_statistics(message: Message) -> None:
    """Показ статистики для администратора"""
    assert message.from_user is not None
    user_id = message.from_user.id
    db = SessionLocal()
    try:
        # Сначала ищем по telegram_id, затем по username
        user = get_user_by_telegram_id(db, user_id)
        logger.info(f"Поиск пользователя по telegram_id {user_id}: {user}")
        
        if not user:
            user = get_user_by_username(db, ADMIN_USERNAME)
            logger.info(f"Поиск пользователя по username {ADMIN_USERNAME}: {user}")
        
        logger.info(f"Проверка админа: user={user}, is_admin={is_admin_user(user)}")
        
        if not is_admin_user(user):
            await message.answer("❌ Только администраторы могут просматривать статистику.")
            return
        
        stats = TelegramService.get_admin_statistics(db)
        
        # Формируем текст статистики
        stats_text = f"📊 Статистика TastySkills\n\n"
        stats_text += f"👑 Менеджеров: {stats['managers_count']}\n"
        stats_text += f"👤 Официантов: {stats['waiters_count']}\n\n"
        
        if stats['managers_info']:
            stats_text += "📋 Детальная информация:\n\n"
            for i, manager in enumerate(stats['managers_info'], 1):
                stats_text += f"{i}. {manager['username']}\n"
                stats_text += f"   Имя: {manager['telegram_name']}\n"
                stats_text += f"   Официантов: {manager['waiters_count']}\n"
                stats_text += f"   Регистрация: {manager['created_at']}\n\n"
        else:
            stats_text += "📋 Менеджеры пока не зарегистрированы."
        
        await message.answer(stats_text)
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики.")
    finally:
        db.close() 