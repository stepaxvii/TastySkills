from aiogram import Router, F
from aiogram.types import Message
from app.infrastructure.database.database import SessionLocal
from app.infrastructure.repositories.crud import get_user_by_telegram_id
from app.presentation.telegram.keyboards import get_waiter_menu_keyboard

waiter_router = Router()

@waiter_router.message(F.text == "🍽️ Работа с меню")
async def open_menu(message: Message) -> None:
    """Открытие меню для официанта"""
    assert message.from_user is not None
    user_id = message.from_user.id
    db = SessionLocal()
    try:
        user = get_user_by_telegram_id(db, user_id)
        if not user or user.role != "waiter":  # type: ignore
            await message.answer("❌ Только официанты могут работать с меню.")
            return
        
        await message.answer(
            "🍽️ Работа с меню\n\n"
            "Откройте веб-интерфейс для работы с меню:\n"
            "http://localhost:8000/\n\n"
            "Там вы сможете просматривать меню ресторана вашего менеджера."
        )
    except Exception as e:
        await message.answer("❌ Произошла ошибка при открытии меню.")
    finally:
        db.close() 