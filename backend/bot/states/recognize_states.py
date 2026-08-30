from aiogram.fsm.state import State, StatesGroup


class RecognizeState(StatesGroup):
    waiting_for_product_list_approval = State()
    waiting_for_choose_recipe = State()
    waiting_for_cooking = State()

