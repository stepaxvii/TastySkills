from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_registration_choice_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👑 Регистрация менеджера", callback_data="register_manager")
        ],
        [
            InlineKeyboardButton(text="👤 Регистрация по приглашению", callback_data="register_invitation")
        ]
    ])
    return keyboard

def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для администратора"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👑 Пригласить менеджера")],
            [KeyboardButton(text="📊 Статистика")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_manager_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для менеджера"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽️ Работа с меню")],
            [KeyboardButton(text="📋 Ссылка для регистрации")],
            [KeyboardButton(text="👥 Мои официанты")],
            [KeyboardButton(text="📊 Статистика официантов")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_waiter_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для официанта (пока пустая)"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽️ Работа с меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard 