from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния для процесса регистрации"""
    waiting_for_registration_choice = State()
    waiting_for_invitation = State()
    waiting_for_username = State()
    waiting_for_password = State() 