from aiogram import Router
from aiogram.types import Message

misc_router = Router()

@misc_router.message()
async def echo_message(message: Message) -> None:
    await message.answer(
        "Используйте /start для регистрации или /help для справки."
    ) 