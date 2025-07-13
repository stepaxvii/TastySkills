from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_registration_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа регистрации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👑 Регистрация менеджера", callback_data="register_manager")
        ],
        [
            InlineKeyboardButton(text="👤 Регистрация по приглашению", callback_data="register_invitation")
        ]
    ])
    return keyboard

def get_manager_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура меню менеджера"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Ссылка для регистрации")],
            [KeyboardButton(text="👥 Мои официанты")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard 