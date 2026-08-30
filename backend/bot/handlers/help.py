from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from aiogram.filters import Command

from services.api_client import withdraw_consent

router = Router()


@router.message(Command("help"))
async def delete_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.reply(
        """
📖 Как пользоваться ботом

AI Sous-Chef

Основные команды

/start — перезапустить бота, сбросить текущий диалог и вернуться к приветственному экрану.
/delete — отозвать согласие на обработку персональных данных.

По фото или списку продуктов можно получить идеи блюд и пошаговый рецепт.

Ингредиенты можно отправить двумя способами:

📸 Способ 1. По фото

Сфотографируйте содержимое холодильника или продукты на столе и отправьте снимок в бот. Система распознает продукты на фото и предложит подходящие рецепты.

Совет: располагайте продукты отдельно друг от друга и следите, чтобы они были хорошо видны на фотографии.

✍️ Способ 2. Текстом

Отправьте список продуктов обычным сообщением.

Пример: курица, картошка, лук, сметана, сыр.
        """
    )
