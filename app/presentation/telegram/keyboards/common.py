from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callback_data.registration import CDCopyInviteCode, CDCopyManagerCode
from .locale import ButtonTexts


def create_copy_code_keyboard(invite_code: str, callback_type: str = "invite") -> InlineKeyboardMarkup:
    """Создание клавиатуры для копирования кода приглашения"""
    if not invite_code:
        return InlineKeyboardMarkup(inline_keyboard=[])
    
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    
    if callback_type == "manager":
        builder.button(
            text=ButtonTexts.COPY_CODE, 
            callback_data=CDCopyManagerCode(invite_code=invite_code)
        )
    else:
        builder.button(
            text=ButtonTexts.COPY_CODE, 
            callback_data=CDCopyInviteCode(invite_code=invite_code)
        )
    
    return builder.as_markup() 