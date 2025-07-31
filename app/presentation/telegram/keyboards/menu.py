from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from .locale import ButtonTexts


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для администратора"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ButtonTexts.INVITE_MANAGER)],
            [KeyboardButton(text=ButtonTexts.STATISTICS)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_manager_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для менеджера"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ButtonTexts.WORK_WITH_MENU)],
            [KeyboardButton(text=ButtonTexts.INVITATION_LINK)],
            [KeyboardButton(text=ButtonTexts.MY_WAITERS)],
            [KeyboardButton(text=ButtonTexts.WAITER_STATISTICS)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_waiter_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для официанта"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ButtonTexts.WAITER_MENU)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard 