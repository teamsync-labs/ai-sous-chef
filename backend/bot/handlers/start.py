import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from aiogram.filters import CommandStart

from keyboards.consent import keyboard_consent_builder, ConsentCallback
from services.api_client import record_consent
from states.accept_states import AcceptConsent

router = Router()

PDN_CONSENT_URL = os.getenv("CONSENT_PUBLIC_BASE")


async def send_first_consent_message(message: Message):
    await message.answer(
        """
Привет! Я AI Sous-Chef — по фото или списку продуктов подберу рецепт.

На фото не должно быть людей и документов. Только продукты.

Политика конфиденциальности — по кнопке ниже. Нажимая «Принимаю», вы подтверждаете, что ознакомились с политикой.
""",
        reply_markup=keyboard_consent_builder(
            ("Политика конфиденциальности", PDN_CONSENT_URL + "/policy")
        )
    )


async def send_second_consent_message(message: Message):
    await message.answer(
        """
И последний шаг перед началом.

Согласие на обработку персональных данных — текст по кнопке ниже.

Нажимая «Даю согласие», вы даёте согласие на обработку персональных данных. Отозвать — /delete.
""",
        reply_markup=keyboard_consent_builder(
            ("Согласие на обработку Персональных Данных", PDN_CONSENT_URL + "/pdn-consent"),
            question_num=2
        )
    )


@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    user_data = await state.get_data()
    if user_data.get("is_accept_consents"):
        await message.reply(
            "Вы уже прошли регистрацию. Для отзыва согласия на обработку персональных данных /delete")
        return

    await state.set_state(AcceptConsent.waiting_for_accept_first_consent)
    await send_first_consent_message(message)


@router.callback_query(ConsentCallback.filter(F.question == 1), AcceptConsent.waiting_for_accept_first_consent)
async def on_first_consent_callback(cb: CallbackQuery, callback_data: ConsentCallback, state: FSMContext):
    if not callback_data.consent:
        await cb.message.delete()
        await send_first_consent_message(cb.message)
        return

    await record_consent(external_id=str(cb.from_user.id), consent_type="privacy", action="granted")
    await state.set_state(AcceptConsent.waiting_for_accept_second_consent)
    await send_second_consent_message(cb.message)


@router.callback_query(ConsentCallback.filter(F.question == 2), AcceptConsent.waiting_for_accept_second_consent)
async def on_second_consent_callback(cb: CallbackQuery, callback_data: ConsentCallback, state: FSMContext):
    if not callback_data.consent:
        await cb.message.delete()
        await send_second_consent_message(cb.message)
        return

    await record_consent(external_id=str(cb.from_user.id), consent_type="pdn", action="granted")
    await state.set_data({"is_accept_consents": True})
    await state.set_state(None)
    await cb.message.answer(
        "Согласия приняты. Можете пользоваться ботом. Для этого отправьте фото/текст с продуктами")
