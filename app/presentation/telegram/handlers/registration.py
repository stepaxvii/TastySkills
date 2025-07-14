import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.domain.entities.telegram_states import RegistrationStates
from app.application.services.telegram_service import TelegramService
from app.presentation.telegram.keyboards import get_registration_choice_keyboard, get_manager_menu_keyboard
from app.infrastructure.database.database import SessionLocal
from app.infrastructure.repositories.crud import get_user_by_telegram_id, get_user_by_username, create_user
from app.domain.entities.schemas import UserCreate
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = os.getenv("ADMIN_ID", "861742986")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "boba")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "paper1234")

logger = logging.getLogger(__name__)
registration_router = Router()

@registration_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id # type: ignore
    db = SessionLocal()
    try:
        if str(user_id) == ADMIN_ID:
            admin = get_user_by_username(db, ADMIN_USERNAME)
            if not admin:
                user_data = UserCreate(
                    username=ADMIN_USERNAME,
                    password=ADMIN_PASSWORD,
                    role="admin"
                )
                create_user(db, user_data)
                await message.answer(f"✅\nЛогин: {ADMIN_USERNAME}\nПароль: {ADMIN_PASSWORD}")
                return
            else:
                await message.answer(f"👑 Аккаунт администратора {ADMIN_USERNAME} уже существует.")
                return
        user = get_user_by_telegram_id(db, user_id)
        if user:
            if user.role == "admin":  # type: ignore
                await message.answer(
                    f"👋 Добро пожаловать, {user.telegram_first_name or user.username}!\n\n"
                    f"👑 Роль: Администратор\n"
                    f"🔗 Веб-интерфейс: http://...\n\n"
                    f"Вы можете управлять всей системой через веб-интерфейс."
                )
            elif user.role == "manager":  # type: ignore
                await message.answer(
                    f"👋 Добро пожаловать, {user.telegram_first_name or user.username}!\n\n"
                    f"👑 Роль: Менеджер\n"
                    f"🔗 Веб-интерфейс: http://...\n\n"
                    f"Используйте кнопки ниже для управления:",
                    reply_markup=get_manager_menu_keyboard()
                )
            else:  # waiter
                await message.answer(
                    f"👋 Добро пожаловать, {user.telegram_first_name or user.username}!\n\n"
                    f"👤 Роль: Официант\n"
                    f"🔗 Веб-интерфейс: http://...\n\n"
                    f"Используйте веб-интерфейс для работы с меню."
                )
            return
        start_param = message.text.split()[1] if message.text and len(message.text.split()) > 1 else None
        if start_param and start_param.startswith("invite_"):
            invitation_code = start_param[7:]
            invitation_data = TelegramService.process_invitation_code(db, invitation_code)
            if invitation_data:
                if invitation_data["type"] == "manager_link":
                    await state.update_data(
                        registration_type="waiter",
                        manager_id=invitation_data["manager_id"]
                    )
                    await state.set_state(RegistrationStates.waiting_for_username)
                    await message.answer(
                        f"👤 Регистрация по приглашению менеджера\n\n"
                        f"✅ Приглашение принято!\n"
                        f"Менеджер: {invitation_data['manager_username']}\n"
                        f"Вы будете зарегистрированы как официант.\n\n"
                        f"Введите логин для входа в систему:\n(разрешены только латинские буквы, цифры и символы)"
                    )
                else:
                    await state.update_data(
                        registration_type="waiter",
                        invitation_id=invitation_data["invitation_id"],
                        manager_id=invitation_data["manager_id"]
                    )
                    await state.set_state(RegistrationStates.waiting_for_username)
                    await message.answer(
                        f"👤 Регистрация по приглашению\n\n"
                        f"✅ Код приглашения принят!\n"
                        f"Вы будете зарегистрированы как официант.\n\n"
                        f"Введите логин для входа в систему:\n(разрешены только латинские буквы, цифры и символы)"
                    )
            else:
                await message.answer(
                    "❌ Неверная ссылка приглашения.\n\n"
                    "Выберите тип регистрации:",
                    reply_markup=get_registration_choice_keyboard()
                )
                await state.set_state(RegistrationStates.waiting_for_registration_choice)
        else:
            await message.answer(
                "🤖 TastySkills Bot\n\n"
                "Добро пожаловать! Для начала работы необходимо зарегистрироваться.\n\n"
                "Выберите тип регистрации:",
                reply_markup=get_registration_choice_keyboard()
            )
            await state.set_state(RegistrationStates.waiting_for_registration_choice)
    except Exception as e:
        logger.error(f"Ошибка при обработке команды start: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз.")
    finally:
        db.close()

@registration_router.callback_query(lambda c: c.data in ["register_manager", "register_invitation"])
async def process_registration_choice(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    if callback_query.data == "register_manager":
        await state.update_data(registration_type="manager")
        await state.set_state(RegistrationStates.waiting_for_username)
        if callback_query.message:
            await callback_query.message.answer(
                "👑 Регистрация менеджера\n\n"
                "Введите логин для входа в систему:\n(разрешены только латинские буквы, цифры и символы)"
            )
    else:
        await state.update_data(registration_type="waiter")
        await state.set_state(RegistrationStates.waiting_for_invitation)
        if callback_query.message:
            await callback_query.message.answer(
                "👤 Регистрация по приглашению\n\n"
                "Введите код приглашения от менеджера:"
            )

@registration_router.message(RegistrationStates.waiting_for_invitation)
async def process_invitation(message: Message, state: FSMContext) -> None:
    invitation_code = message.text.strip() if message.text else ""
    db = SessionLocal()
    try:
        invitation_data = TelegramService.process_invitation_code(db, invitation_code)
        if invitation_data:
            if invitation_data["type"] == "manager_link":
                await state.update_data(
                    manager_id=invitation_data["manager_id"]
                )
            else:
                await state.update_data(
                    invitation_id=invitation_data["invitation_id"],
                    manager_id=invitation_data["manager_id"]
                )
            await state.set_state(RegistrationStates.waiting_for_username)
            await message.answer(
                "✅ Код приглашения принят!\n\n"
                "Введите логин для входа в систему:\n(разрешены только латинские буквы, цифры и символы)"
            )
        else:
            await message.answer(
                "❌ Неверный код приглашения.\n"
                "Попросите вашего менеджера выслать ссылку для приглашения."
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке приглашения: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз.")
    finally:
        db.close()

@registration_router.message(RegistrationStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext) -> None:
    username = message.text.strip() if message.text else ""
    is_valid, error_msg = TelegramService.validate_username(username)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\nПопробуйте еще раз:")
        return
    await state.update_data(username=username)
    await state.set_state(RegistrationStates.waiting_for_password)
    await message.answer(
        "Введите пароль для входа в систему:\n"
        "(минимум 6 символов)"
    )

@registration_router.message(RegistrationStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext) -> None:
    password = message.text if message.text else ""
    is_valid, error_msg = TelegramService.validate_password(password)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\nПопробуйте еще раз:")
        return
    await state.update_data(password=password)
    user_data = await state.get_data()
    registration_type = user_data.get('registration_type', 'waiter')
    if registration_type == "manager":
        await complete_registration(message, state, "manager")
    else:
        await complete_registration(message, state, "waiter")

async def complete_registration(message: Message, state: FSMContext, role: str = "waiter") -> None:
    user_data = await state.get_data()
    username = user_data.get('username')
    password = user_data.get('password')
    logger.info(f"Завершение регистрации: username={username}, role={role}")
    if not username or not password:
        await message.answer("❌ Ошибка: отсутствуют данные для регистрации")
        return
    logger.info(f"Создание пользователя: {username}, роль: {role}")
    db = SessionLocal()
    try:
        assert message.from_user is not None
        telegram_data = {
            'id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name
        }
        user = TelegramService.register_user(
            db=db,
            username=username,
            password=password,
            role=role,
            telegram_data=telegram_data,
            manager_id=user_data.get('manager_id'),
            invitation_id=user_data.get('invitation_id')
        )
        logger.info(f"Пользователь создан с ID: {user.id}")
        if role == "manager":
            await message.answer(
                f"🎉 Регистрация менеджера завершена!\n\n"
                f"👤 Логин: {username}\n"
                f"👑 Роль: Менеджер\n\n"
                f"Теперь вы можете создавать приглашения для официантов.\n"
                f"Используйте кнопку '📋 Ссылка для регистрации'",
                reply_markup=get_manager_menu_keyboard()
            )
        else:
            await message.answer(
                f"🎉 Регистрация завершена!\n\n"
                f"👤 Логин: {username}\n"
                f"👑 Роль: Официант\n\n"
                f"Теперь вы можете использовать веб-интерфейс для работы с меню.\n"
                f"Перейдите по ссылке: http://..."
            )
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        await message.answer("❌ Произошла ошибка при регистрации. Попробуйте еще раз.")
    finally:
        db.close() 