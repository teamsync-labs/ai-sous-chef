from aiogram.fsm.state import State, StatesGroup


class AcceptConsent(StatesGroup):
    waiting_for_accept_first_consent = State()
    waiting_for_accept_second_consent = State()
