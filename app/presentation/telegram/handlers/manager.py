from aiogram import Router, F, Bot
from aiogram.types import Message
from app.application.services.telegram_service import TelegramService
from aiogram.types import CallbackQuery
from app.presentation.telegram.utils import (
    get_db_session, get_user_safely, is_manager_user,
    create_copy_code_keyboard, extract_invite_code_from_link,
    get_role_permission_message, handle_database_error
)

manager_router = Router()

@manager_router.message(F.text == "📋 Ссылка для регистрации")
async def create_invitation(message: Message, bot: Bot) -> None:
    assert message.from_user is not None
    user_id = message.from_user.id
    
    async with get_db_session() as db:
        try:
            user = get_user_safely(db, user_id)
            if not is_manager_user(user):
                await message.answer(get_role_permission_message("manager", "создавать приглашения"))
                return
            
            bot_username = (await bot.get_me()).username or ""
            waiter_link = TelegramService.create_manager_invitation_link(db, user, bot_username)
            
            # Извлекаем код приглашения и создаем клавиатуру
            invite_code = extract_invite_code_from_link(waiter_link)
            copy_code_kb = create_copy_code_keyboard(invite_code, "copy_invite_code")
            
            await message.answer(
                f"📋 Регистрация в TastySkills:\n\n"
                f"🔗 {waiter_link}\n"
                + (f"Код для регистрации: {invite_code}\n" if invite_code else ""),
                reply_markup=copy_code_kb
            )
            await message.answer(
                "Перешлите сообщение с ссылкой сотруднику, которого хотите пригласить в TastySkills."
            )
        except Exception as e:
            await handle_database_error(message, e, "создании пригласительной ссылки")

# Обработчик для инлайн-кнопки 'Скопировать код'
@manager_router.callback_query(F.data.startswith("copy_invite_code:"))
async def copy_invite_code_callback(callback: CallbackQuery):
    if not callback.data:
        await callback.answer("Нет кода для копирования.", show_alert=True)
        return
    code = callback.data.split(":", 1)[-1]
    if not callback.message:
        await callback.answer("Нет сообщения для отправки кода.", show_alert=True)
        return
    await callback.answer("Код скопирован!", show_alert=False)
    await callback.message.answer(f"Код для регистрации: {code}")

@manager_router.message(F.text == "👥 Мои официанты")
async def show_waiters(message: Message) -> None:
    assert message.from_user is not None
    user_id = message.from_user.id
    
    async with get_db_session() as db:
        try:
            user = get_user_safely(db, user_id)
            if not is_manager_user(user):
                await message.answer(get_role_permission_message("manager", "просматривать список официантов"))
                return
            
            manager_id = int(getattr(user, 'id', 0))
            waiters = TelegramService.get_manager_waiters(db, manager_id)
            if waiters:
                waiters_text = f"👥 Ваши официанты ({len(waiters)}):\n\n"
                for i, waiter in enumerate(waiters, 1):
                    waiters_text += f"{i}. {waiter.username}\n"
                    if waiter.telegram_first_name:  # type: ignore
                        waiters_text += f"   Имя: {waiter.telegram_first_name}\n"
                    waiters_text += f"   Зарегистрирован: {waiter.created_at.strftime('%d.%m.%Y')}\n\n"
            else:
                waiters_text = "👥 У вас пока нет официантов.\nСоздайте приглашение, чтобы добавить официанта."
            await message.answer(waiters_text)
        except Exception as e:
            await handle_database_error(message, e, "получении списка официантов")

@manager_router.message(F.text == "📊 Статистика официантов")
async def show_manager_statistics(message: Message) -> None:
    """Показ статистики официантов для менеджера"""
    assert message.from_user is not None
    user_id = message.from_user.id
    
    async with get_db_session() as db:
        try:
            user = get_user_safely(db, user_id)
            if not is_manager_user(user):
                await message.answer(get_role_permission_message("manager", "просматривать статистику официантов"))
                return
            
            manager_id = int(getattr(user, 'id', 0))
            stats = TelegramService.get_manager_statistics(db, manager_id)
            
            # Формируем текст статистики
            stats_text = f"📊 Статистика официантов\n\n"
            stats_text += f"👤 Всего официантов: {stats['total_waiters']}\n"
            stats_text += f"✅ Активных: {stats['active_waiters']}\n"
            stats_text += f"❌ Неактивных: {stats['inactive_waiters']}\n\n"
            
            if stats['waiters_by_date']:
                stats_text += "📅 Регистрации по датам:\n"
                for date, count in sorted(stats['waiters_by_date'].items()):
                    stats_text += f"   {date}: {count} чел.\n"
                stats_text += "\n"
            
            if stats['waiters_list']:
                stats_text += "📋 Список официантов:\n\n"
                for i, waiter in enumerate(stats['waiters_list'], 1):
                    status = "✅" if waiter['is_active'] else "❌"
                    stats_text += f"{i}. {waiter['username']} {status}\n"
                    stats_text += f"   Имя: {waiter['telegram_name']}\n"
                    stats_text += f"   Регистрация: {waiter['created_at']}\n\n"
            else:
                stats_text += "📋 Официанты пока не зарегистрированы."
            
            await message.answer(stats_text)
        except Exception as e:
            await handle_database_error(message, e, "получении статистики")

@manager_router.message(F.text == "🍽️ Работа с меню")
async def open_menu(message: Message) -> None:
    await message.answer("Откройте меню по ссылке: http://localhost:8000/")

@manager_router.message(F.text == "🍽️ Приступить к созданию ресторана и наполнению меню")
async def start_create_restaurant(message: Message) -> None:
    async with get_db_session() as db:
        try:
            if not message.from_user:
                await message.answer("Ошибка: не удалось определить пользователя Telegram.")
                return
            user = get_user_safely(db, message.from_user.id)
            if not is_manager_user(user):
                await message.answer(get_role_permission_message("manager", "создавать ресторан"))
                return
            
            from app.infrastructure.repositories.crud import get_restaurants_by_manager
            manager_id = int(getattr(user, 'id', 0))
            restaurants = get_restaurants_by_manager(db, manager_id)
            if not restaurants:
                await message.answer(
                    "У вас пока нет ресторана. Перейдите по ссылке для создания ресторана:\n"
                    "http://localhost:8000/manage/restaurants/create"
                )
            else:
                restaurant = restaurants[0]
                await message.answer(
                    f"Ваш ресторан: {restaurant.name}\n"
                    f"Перейдите к наполнению меню: http://localhost:8000/restaurants/{restaurant.id}"
                )
        except Exception as e:
            await handle_database_error(message, e, "создании ресторана")
