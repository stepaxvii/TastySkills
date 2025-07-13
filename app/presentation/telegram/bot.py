import asyncio
from aiogram import Bot, Dispatcher
from app.presentation.telegram.handlers import router
from app.config import TELEGRAM_BOT_TOKEN

async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 