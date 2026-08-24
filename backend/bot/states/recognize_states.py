from aiogram.fsm.state import State, StatesGroup


class RecognizeState(StatesGroup):
    waiting_for_product_list_approval = State()

