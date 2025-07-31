from aiogram import Router, F, Bot
from aiogram.types import Message
from app.application.services.telegram_service import TelegramService
from aiogram.types import CallbackQuery
from app.presentation.telegram.utils import (
    get_db_session, get_user_safely, is_admin_user, 
    extract_invite_code_from_link,
    get_role_permission_message, handle_database_error
)
from app.presentation.telegram.keyboards.common import create_copy_code_keyboard
from app.presentation.telegram.keyboards.callback_data.registration import CDCopyManagerCode
from app.presentation.telegram.keyboards.locale import ButtonTexts
import logging

logger = logging.getLogger(__name__)
admin_router = Router()

@admin_router.message(F.text == ButtonTexts.INVITE_MANAGER)
async def create_manager_invitation(message: Message, bot: Bot) -> None:
    """Создание приглашения для менеджера от админа"""
    assert message.from_user is not None
    user_id = message.from_user.id
    
    async with get_db_session() as db:
        try:
            # Получаем пользователя безопасно
            user = get_user_safely(db, user_id)
            logger.info(f"Поиск пользователя по telegram_id {user_id}: {user}")
            
            if not is_admin_user(user):
                await message.answer(get_role_permission_message("admin", "создавать приглашения для менеджеров"))
                return
            
            bot_username = (await bot.get_me()).username or ""
            manager_link = TelegramService.create_admin_manager_invitation_link(db, user, bot_username)
            
            # Извлекаем код приглашения и создаем клавиатуру
            invite_code = extract_invite_code_from_link(manager_link)
            copy_code_kb = create_copy_code_keyboard(invite_code, "manager")
            
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
            await handle_database_error(message, e, "создании приглашения менеджера")

@admin_router.callback_query(CDCopyManagerCode.filter())
async def copy_manager_code_callback(callback: CallbackQuery):
    """Обработчик для копирования кода приглашения менеджера"""
    if not callback.message:
        await callback.answer("Нет сообщения для отправки кода.", show_alert=True)
        return
    
    # Получаем код из callback данных
    callback_data = CDCopyManagerCode.unpack(callback.data)
    code = callback_data.invite_code
    
    await callback.answer("Код скопирован!", show_alert=False)
    await callback.message.answer(f"Код для регистрации менеджера: {code}")

@admin_router.message(F.text == ButtonTexts.STATISTICS)
async def show_admin_statistics(message: Message) -> None:
    """Показ статистики для администратора"""
    assert message.from_user is not None
    user_id = message.from_user.id
    
    async with get_db_session() as db:
        try:
            # Получаем пользователя безопасно
            user = get_user_safely(db, user_id)
            logger.info(f"Поиск пользователя по telegram_id {user_id}: {user}")
            
            if not is_admin_user(user):
                await message.answer(get_role_permission_message("admin", "просматривать статистику"))
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
            await handle_database_error(message, e, "получении статистики")
