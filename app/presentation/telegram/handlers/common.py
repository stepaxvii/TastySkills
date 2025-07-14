from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from app.infrastructure.database.database import SessionLocal
from app.infrastructure.repositories.crud import get_user_by_telegram_id

common_router = Router()

@common_router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    db = SessionLocal()
    try:
        user = None
        if message.from_user:
            user = get_user_by_telegram_id(db, message.from_user.id)
        if user:
            await message.answer(
                f"🤖 TastySkills\n\n"
                f"Ваши данные для входа в систему:\n"
                f"👤 Логин: {user.username}\n"
                f"🔑 Пароль: (выбранный при регистрации или сброшенный)\n\n"
                f"Если вы забыли пароль, используйте команду /reset_password для его сброса.\n\n"
                f"Доступные команды:\n"
                f"/start - Начать регистрацию\n"
                f"/help - Показать эту справку\n"
                f"/reset_password - Сбросить пароль\n\n"
                f"После регистрации используйте веб-интерфейс для работы с меню."
            )
        else:
            await message.answer(
                "🤖 TastySkills\n\n"
                "Доступные команды:\n"
                "/start - Начать регистрацию\n"
                "/help - Показать эту справку\n"
                "/reset_password - Сбросить пароль\n\n"
                "После регистрации используйте веб-интерфейс для работы с меню."
            )
    finally:
        db.close() 