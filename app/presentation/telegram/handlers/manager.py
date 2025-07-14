from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.infrastructure.database.database import SessionLocal
from app.infrastructure.repositories.crud import get_user_by_telegram_id
from app.application.services.telegram_service import TelegramService
from app.presentation.telegram.keyboards import get_manager_menu_keyboard
from aiogram.types import CallbackQuery

manager_router = Router()

@manager_router.message(F.text == "📋 Ссылка для регистрации")
async def create_invitation(message: Message, bot: Bot) -> None:
    assert message.from_user is not None
    user_id = message.from_user.id
    db = SessionLocal()
    try:
        user = get_user_by_telegram_id(db, user_id)
        if not user or user.role != "manager":  # type: ignore
            await message.answer("❌ Только менеджеры могут создавать приглашения.")
            return
        bot_username = (await bot.get_me()).username or ""
        waiter_link = TelegramService.create_manager_invitation_link(db, user, bot_username)
        # Извлечь код приглашения из ссылки
        invite_code = None
        if waiter_link and 'invite_' in waiter_link:
            invite_code = waiter_link.split('invite_')[-1]
        # Клавиатура для копирования кода
        copy_code_kb = None
        if invite_code:
            copy_code_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Скопировать код", callback_data=f"copy_invite_code:{invite_code}")]
                ]
            )
        if user.waiter_link == waiter_link:  # type: ignore
            await message.answer(
                f"📋 Регистрация в TastySkills:\n\n"
                f"🔗 {waiter_link}\n"
                + (f"Код для регистрации: {invite_code}\n" if invite_code else ""),
                reply_markup=copy_code_kb
            )
            await message.answer(
                "Перешлите сообщение с ссылкой сотруднику, которого хотите пригласить в TastySkills."
            )
        else:
            await message.answer(
                f"📋 Регистрация в TastySkills:\n\n"
                f"🔗 {waiter_link}\n"
                + (f"Код для регистрации: {invite_code}\n" if invite_code else ""),
                reply_markup=copy_code_kb
            )
    except Exception as e:
        await message.answer("❌ Произошла ошибка при создании пригласительной ссылки.")
    finally:
        db.close()

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
    db = SessionLocal()
    try:
        user = get_user_by_telegram_id(db, user_id)
        if not user or user.role != "manager":  # type: ignore
            await message.answer("❌ Только менеджеры могут просматривать список официантов.")
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
        await message.answer("❌ Произошла ошибка при получении списка официантов.")
    finally:
        db.close()

@manager_router.message(F.text == "🍽️ Работа с меню")
async def open_menu(message: Message) -> None:
    await message.answer("Откройте меню по ссылке: http://localhost:8000/")

@manager_router.message(F.text == "🍽️ Приступить к созданию ресторана и наполнению меню")
async def start_create_restaurant(message: Message) -> None:
    db = SessionLocal()
    try:
        if not message.from_user:
            await message.answer("Ошибка: не удалось определить пользователя Telegram.")
            return
        user = get_user_by_telegram_id(db, message.from_user.id)
        if user is None:
            await message.answer("❌ Только менеджеры могут создавать ресторан.")
            return
        if getattr(user, "role", None) != "manager":
            await message.answer("❌ Только менеджеры могут создавать ресторан.")
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
    finally:
        db.close() 