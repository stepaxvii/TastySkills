import os
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.domain.entities.telegram_states import RegistrationStates
from app.application.services.telegram_service import TelegramService
from app.presentation.telegram.keyboards.menu import get_manager_menu_keyboard, get_admin_menu_keyboard, get_waiter_menu_keyboard
from app.presentation.telegram.keyboards.locale import ButtonTexts
from app.infrastructure.repositories.crud import get_user_by_telegram_id, get_user_by_username, create_user
from app.domain.entities.schemas import UserCreate
from app.presentation.telegram.utils import get_db_session, send_welcome_message, handle_database_error
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = os.getenv("ADMIN_ID", "861742986")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "boba")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "paper1234")

logger = logging.getLogger(__name__)
registration_router = Router()

@registration_router.message(Command("myid"))
async def cmd_myid(message: Message) -> None:
    """Команда для получения Telegram ID пользователя"""
    user_id = message.from_user.id  # type: ignore
    username = message.from_user.username or "Не указан"
    first_name = message.from_user.first_name or "Не указано"
    
    await message.answer(
        f"🔍 Ваши данные:\n\n"
        f"🆔 Telegram ID: {user_id}\n"
        f"👤 Username: @{username}\n"
        f"📝 Имя: {first_name}\n\n"
        f"Текущий ADMIN_ID в системе: {ADMIN_ID}"
    )

@registration_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id # type: ignore
    async with get_db_session() as db:
        try:
            # Отладочная информация
            logger.info(f"Пользователь {user_id} запустил бота. ADMIN_ID: {ADMIN_ID}")
            
            # Проверяем, является ли пользователь админом
            if str(user_id) == ADMIN_ID:
                admin = get_user_by_username(db, ADMIN_USERNAME)
                if not admin:
                    user_data = UserCreate(
                        username=ADMIN_USERNAME,
                        password=ADMIN_PASSWORD,
                        role="admin"
                    )
                    admin = create_user(db, user_data)
                    
                    # Устанавливаем Telegram данные для админа
                    assert message.from_user is not None
                    admin.telegram_id = message.from_user.id  # type: ignore
                    admin.telegram_username = message.from_user.username  # type: ignore
                    admin.telegram_first_name = message.from_user.first_name  # type: ignore
                    admin.telegram_last_name = message.from_user.last_name  # type: ignore
                    admin.is_telegram_user = True  # type: ignore
                    db.commit()
                    
                    await message.answer(
                        f"✅ Администратор создан!\n\n"
                        f"Логин: {ADMIN_USERNAME}\n"
                        f"Пароль: {ADMIN_PASSWORD}\n\n"
                        f"Используйте кнопки ниже для управления:",
                        reply_markup=get_admin_menu_keyboard()
                    )
                    return
                else:
                    # Если админ уже существует, показываем приветствие с клавиатурой
                    await send_welcome_message(message, admin, "admin")
                    return
            
            # Для всех остальных пользователей проверяем, есть ли параметр приглашения
            start_param = message.text.split()[1] if message.text and len(message.text.split()) > 1 else None
            
            if not start_param or not start_param.startswith("invite_"):
                # Если нет приглашения, показываем сообщение о том, что нужна ссылка
                await message.answer(
                    "🤖 TastySkills Bot\n\n"
                    "Для регистрации в системе вам необходима пригласительная ссылка.\n\n"
                    "Обратитесь к администратору или менеджеру для получения ссылки."
                )
                return
            
            # Обрабатываем приглашение
            invitation_code = start_param[7:]
            invitation_data = TelegramService.process_invitation_code(db, invitation_code)
            
            if not invitation_data:
                await message.answer(
                    "❌ Неверная ссылка приглашения.\n\n"
                    "Обратитесь к администратору или менеджеру для получения корректной ссылки."
                )
                return
            
            # Проверяем, не зарегистрирован ли уже пользователь
            existing_user = get_user_by_telegram_id(db, user_id)
            if existing_user:
                # Пользователь уже зарегистрирован, показываем соответствующую клавиатуру
                await send_welcome_message(message, existing_user, existing_user.role)  # type: ignore
                return
            
            # Начинаем процесс регистрации по приглашению
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
            elif invitation_data["type"] == "admin_manager_invitation":
                await state.update_data(
                    registration_type="manager",
                    invitation_id=invitation_data["invitation_id"]
                )
                await state.set_state(RegistrationStates.waiting_for_username)
                await message.answer(
                    f"👑 Регистрация менеджера по приглашению администратора\n\n"
                    f"✅ Приглашение принято!\n"
                    f"Вы будете зарегистрированы как менеджер.\n\n"
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
        except Exception as e:
            await handle_database_error(message, e, "обработке команды start")

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
    
    async with get_db_session() as db:
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
                    f"Используйте кнопку '{ButtonTexts.INVITATION_LINK}'",
                    reply_markup=get_manager_menu_keyboard()
                )
            else:
                await message.answer(
                    f"🎉 Регистрация завершена!\n\n"
                    f"👤 Логин: {username}\n"
                    f"👑 Роль: Официант\n\n"
                    f"Теперь вы можете использовать веб-интерфейс для работы с меню.\n"
                    f"Перейдите по ссылке: http://...",
                    reply_markup=get_waiter_menu_keyboard()
                )
            await state.clear()
        except Exception as e:
            await handle_database_error(message, e, "регистрации")
