from aiogram.filters.callback_data import CallbackData


class CDRegisterManager(CallbackData, prefix="register_manager"):
    """Callback данные для регистрации менеджера"""
    pass


class CDRegisterInvitation(CallbackData, prefix="register_invitation"):
    """Callback данные для регистрации по приглашению"""
    pass


class CDCopyInviteCode(CallbackData, prefix="copy_invite_code"):
    """Callback данные для копирования кода приглашения"""
    invite_code: str


class CDCopyManagerCode(CallbackData, prefix="copy_manager_code"):
    """Callback данные для копирования кода приглашения менеджера"""
    invite_code: str 