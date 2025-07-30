from aiogram import Router, F
from aiogram.types import Message
from app.presentation.telegram.utils import (
    get_db_session, get_user_safely, is_waiter_user,
    get_role_permission_message, handle_database_error
)

waiter_router = Router()

@waiter_router.message(F.text == "🍽️ Работа с меню")
async def open_menu(message: Message) -> None:
    """Открытие меню для официанта"""
    assert message.from_user is not None
    user_id = message.from_user.id
    
    async with get_db_session() as db:
        try:
            user = get_user_safely(db, user_id)
            if not is_waiter_user(user):
                await message.answer(get_role_permission_message("waiter", "работать с меню"))
                return
            
            await message.answer(
                "🍽️ Работа с меню\n\n"
                "Откройте веб-интерфейс для работы с меню:\n"
                "http://localhost:8000/\n\n"
                "Там вы сможете просматривать меню ресторана вашего менеджера."
            )
        except Exception as e:
            await handle_database_error(message, e, "открытии меню")
