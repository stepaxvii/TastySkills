from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.domain.entities.telegram_states import RegistrationStates
from app.application.services.telegram_service import TelegramService
from app.infrastructure.database.database import SessionLocal

password_router = Router()

@password_router.message(Command("reset_password"))
async def cmd_reset_password(message: Message, state: FSMContext) -> None:
    db = SessionLocal()
    try:
        user = None
        if message.from_user:
            from app.infrastructure.repositories.crud import get_user_by_telegram_id
            user = get_user_by_telegram_id(db, message.from_user.id)
        if not user:
            await message.answer("❌ Вы не зарегистрированы в системе. Используйте /start для регистрации.")
            return
        await state.set_state(RegistrationStates.waiting_for_new_password)
        await message.answer(
            "Введите новый пароль для входа в систему:\n(минимум 6 символов)"
        )
    finally:
        db.close()

@password_router.message(RegistrationStates.waiting_for_new_password)
async def process_new_password(message: Message, state: FSMContext) -> None:
    new_password = message.text if message.text else ""
    is_valid, error_msg = TelegramService.validate_password(new_password)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\nПопробуйте еще раз:")
        return
    db = SessionLocal()
    try:
        user = None
        if message.from_user:
            from app.infrastructure.repositories.crud import get_user_by_telegram_id
            user = get_user_by_telegram_id(db, message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Попробуйте снова или зарегистрируйтесь.")
            await state.clear()
            return
        from app.presentation.api.auth import get_password_hash
        setattr(user, 'hashed_password', get_password_hash(new_password))
        db.commit()
        await message.answer("✅ Пароль успешно изменён! Теперь вы можете использовать новый пароль для входа в систему через веб-интерфейс.")
        await state.clear()
    finally:
        db.close() 