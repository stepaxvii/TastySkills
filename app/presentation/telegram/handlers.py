import os
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.domain.entities.telegram_states import RegistrationStates
from app.application.services.telegram_service import TelegramService
from app.presentation.telegram.keyboards.registration import get_registration_choice_keyboard
from app.presentation.telegram.keyboards.menu import get_manager_menu_keyboard
from app.presentation.telegram.keyboards.callback_data.registration import CDRegisterManager, CDRegisterInvitation, CDCopyInviteCode
from app.presentation.telegram.keyboards.locale import ButtonTexts
from app.infrastructure.database.database import SessionLocal
from app.infrastructure.repositories.crud import get_user_by_telegram_id, get_user_by_username, create_user
from app.domain.entities.schemas import UserCreate
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = os.getenv("ADMIN_ID", "861742986")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "boba")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "paper1234")

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id # type: ignore
    
    db = SessionLocal()
    try:
        # --- АВТОСОЗДАНИЕ АДМИНА ---
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
        
        # Проверяем, зарегистрирован ли пользователь
        user = get_user_by_telegram_id(db, user_id)
        
        if user:
            # Пользователь уже зарегистрирован
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
        
        # Проверяем параметры start для приглашений
        start_param = message.text.split()[1] if message.text and len(message.text.split()) > 1 else None
        
        if start_param and start_param.startswith("invite_"):
            # Обработка пригласительной ссылки
            invitation_code = start_param[7:]  # Убираем "invite_"
            
            # Обрабатываем код приглашения
            invitation_data = TelegramService.process_invitation_code(db, invitation_code)
            
            if invitation_data:
                if invitation_data["type"] == "manager_link":
                    # Сохраняем данные менеджера и начинаем регистрацию официанта
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
                else:  # invitation
                    # Сохраняем данные приглашения и начинаем регистрацию официанта
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
            # Обычная регистрация
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

@router.callback_query(CDRegisterManager.filter() | CDRegisterInvitation.filter())
async def process_registration_choice(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора типа регистрации"""
    await callback_query.answer()
    
    if isinstance(callback_query.data, CDRegisterManager):
        await state.update_data(registration_type="manager")
        await state.set_state(RegistrationStates.waiting_for_username)
        if callback_query.message:
            await callback_query.message.answer(
                "👑 Регистрация менеджера\n\n"
                "Введите логин для входа в систему:\n(разрешены только латинские буквы, цифры и символы)"
            )
    else:  # register_invitation
        await state.update_data(registration_type="waiter")
        await state.set_state(RegistrationStates.waiting_for_invitation)
        if callback_query.message:
            await callback_query.message.answer(
                "👤 Регистрация по приглашению\n\n"
                "Введите код приглашения от менеджера:"
            )

@router.message(RegistrationStates.waiting_for_invitation)
async def process_invitation(message: Message, state: FSMContext) -> None:
    """Обработка ввода кода приглашения"""
    invitation_code = message.text.strip() if message.text else ""
    
    db = SessionLocal()
    try:
        # Обрабатываем код приглашения
        invitation_data = TelegramService.process_invitation_code(db, invitation_code)
        
        if invitation_data:
            if invitation_data["type"] == "manager_link":
                await state.update_data(
                    manager_id=invitation_data["manager_id"]
                )
            else:  # invitation
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

@router.message(RegistrationStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext) -> None:
    """Обработка ввода логина"""
    username = message.text.strip() if message.text else ""
    
    # Валидация логина
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

@router.message(RegistrationStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext) -> None:
    """Обработка ввода пароля"""
    password = message.text if message.text else ""
    
    # Валидация пароля
    is_valid, error_msg = TelegramService.validate_password(password)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\nПопробуйте еще раз:")
        return
    
    await state.update_data(password=password)
    
    # Определяем роль на основе типа регистрации
    user_data = await state.get_data()
    registration_type = user_data.get('registration_type', 'waiter')
    
    if registration_type == "manager":
        await complete_registration(message, state, "manager")
    else:
        await complete_registration(message, state, "waiter")

async def complete_registration(message: Message, state: FSMContext, role: str = "waiter") -> None:
    """Завершение регистрации"""
    user_data = await state.get_data()
    username = user_data.get('username')
    password = user_data.get('password')
    
    logger.info(f"Завершение регистрации: username={username}, role={role}")
    
    if not username or not password:
        await message.answer("❌ Ошибка: отсутствуют данные для регистрации")
        return
    
    logger.info(f"Создание пользователя: {username}, роль: {role}")
    
    # Создаем пользователя
    db = SessionLocal()
    try:
        assert message.from_user is not None
        
        # Подготавливаем данные Telegram
        telegram_data = {
            'id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name
        }
        
        # Регистрируем пользователя
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
                f"Перейдите по ссылке: http://..."
            )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        await message.answer("❌ Произошла ошибка при регистрации. Попробуйте еще раз.")
    finally:
        db.close()

# Обработчики меню менеджера
@router.message(F.text == ButtonTexts.CREATE_INVITATION)
async def create_invitation(message: Message, bot: Bot) -> None:
    """Создание приглашения для официанта"""
    assert message.from_user is not None
    user_id = message.from_user.id
    db = SessionLocal()
    
    try:
        user = get_user_by_telegram_id(db, user_id)
        if not user or user.role != "manager":  # type: ignore
            await message.answer("❌ Только менеджеры могут создавать приглашения.")
            return
        
        # Создаем или получаем постоянную ссылку
        bot_username = (await bot.get_me()).username or ""
        waiter_link = TelegramService.create_manager_invitation_link(db, user, bot_username)
        
        if user.waiter_link == waiter_link:  # type: ignore
            # Ссылка уже существовала
            await message.answer(
                f"📋 Регистрация в TastySkills:\n\n"
                f"🔗 {waiter_link}\n\n"
            )
            await message.answer(
                "Перешлите сообщение с ссылкой сотруднику, которого хотите пригласить в TastySkills."
            )
        else:
            # Ссылка была создана
            await message.answer(
                f"📋 Регистрация в TastySkills:\n\n"
                f"🔗 {waiter_link}\n\n"
            )
        
    except Exception as e:
        logger.error(f"Ошибка при создании приглашения: {e}")
        await message.answer("❌ Произошла ошибка при создании пригласительной ссылки.")
    finally:
        db.close()

@router.message(F.text == ButtonTexts.MY_WAITERS)
async def show_waiters(message: Message) -> None:
    """Показать список официантов менеджера"""
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
        logger.error(f"Ошибка при получении списка официантов: {e}")
        await message.answer("❌ Произошла ошибка при получении списка официантов.")
    finally:
        db.close()

@router.message(F.text == ButtonTexts.CREATE_RESTAURANT)
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
        # Теперь user гарантированно не None
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

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработчик команды /help"""
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

@router.message(Command("reset_password"))
async def cmd_reset_password(message: Message, state: FSMContext) -> None:
    """Обработчик команды /reset_password"""
    db = SessionLocal()
    try:
        user = None
        if message.from_user:
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

@router.message(RegistrationStates.waiting_for_new_password)
async def process_new_password(message: Message, state: FSMContext) -> None:
    """Обработка нового пароля для сброса"""
    new_password = message.text if message.text else ""
    is_valid, error_msg = TelegramService.validate_password(new_password)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\nПопробуйте еще раз:")
        return
    user_data = await state.get_data()
    db = SessionLocal()
    try:
        user = None
        if message.from_user:
            user = get_user_by_telegram_id(db, message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Попробуйте снова или зарегистрируйтесь.")
            await state.clear()
            return
        # Обновляем пароль пользователя
        from app.presentation.api.auth import get_password_hash
        setattr(user, "hashed_password", get_password_hash(new_password))
        db.commit()
        await message.answer("✅ Пароль успешно изменён! Теперь вы можете использовать новый пароль для входа в систему через веб-интерфейс.")
        await state.clear()
    finally:
        db.close()

@router.callback_query(CDCopyInviteCode.filter())
async def copy_invite_code(callback_query: CallbackQuery) -> None:
    """Обработка копирования кода приглашения"""
    await callback_query.answer("📋 Код приглашения скопирован в буфер обмена!")

@router.message()
async def echo_message(message: Message) -> None:
    """Обработка всех остальных сообщений"""
    await message.answer(
        "Используйте /start для регистрации или /help для справки."
    ) 