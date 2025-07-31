from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callback_data.registration import CDRegisterManager, CDRegisterInvitation
from .locale import ButtonTexts


def get_registration_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа регистрации"""
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    
    builder.button(
        text=ButtonTexts.REGISTER_MANAGER, 
        callback_data=CDRegisterManager()
    )
    builder.button(
        text=ButtonTexts.REGISTER_INVITATION, 
        callback_data=CDRegisterInvitation()
    )
    
    # Размещаем кнопки в два ряда
    builder.adjust(1)
    
    return builder.as_markup() 