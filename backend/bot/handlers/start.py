import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from aiogram.filters import CommandStart

from keyboards.consent import keyboard_consent_builder, ConsentCallback

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
async def start_cmd(message: Message):
    await send_first_consent_message(message)


@router.callback_query(ConsentCallback.filter(F.question == 1))
async def on_first_consent_callback(cb: CallbackQuery, callback_data: ConsentCallback):
    if callback_data.consent:
        await send_second_consent_message(cb.message)
    else:
        await cb.message.delete()
        await send_first_consent_message(cb.message)


@router.callback_query(ConsentCallback.filter(F.question == 2))
async def on_second_consent_callback(cb: CallbackQuery, callback_data: ConsentCallback):
    if callback_data.consent:
        await cb.message.answer(
            "Ответ на второй вопрос зачтен")
    else:
        await cb.message.delete()
        await send_second_consent_message(cb.message)
