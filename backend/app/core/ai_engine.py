import base64
import json
import re

from app.api.api_models import RecipesResult, RecognizeResult, RecipesInput, RecognizeInput
from abc import ABC, abstractmethod

from app.core.config import settings
from openai import AsyncOpenAI


class AIServiceError(RuntimeError):
    pass


class AIServiceUnavailableError(AIServiceError):
    pass


class ProductsNotFoundError(AIServiceError):
    pass


class AIProtocol(ABC):
    @staticmethod
    @abstractmethod
    def recognize_products(recognize_input: RecognizeInput) -> RecognizeResult:
        pass

    @staticmethod
    @abstractmethod
    def generate_recipes(recipes_input: RecipesInput) -> RecipesResult:
        pass


class AIEngine(AIProtocol):
    """
    TODO здесь должно выбрасываться исключение AIServiceUnavailableError в случае ошибки внешнего ИИ сервиса и ProductsNotFoundError,
    если продукты не распознаны - ProductsNotFoundError
    """
    AI_API_URL = "https://ai.api.cloud.yandex.net/v1"

    YANDEX_API_KEY = settings.YANDEX_API_KEY
    YANDEX_FOLDER_ID = settings.YANDEX_FOLDER_ID

    MODEL_FOR_CV = f"gpt://{YANDEX_FOLDER_ID}/qwen3.6-35b-a3b/latest"
    MODEL_FOR_LLM = f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest"

    @staticmethod
    def _parse_products(raw_text: str) -> list[str]:
        """
        Извлекает список продуктов из ответа модели.
        Работает с JSON-массивами, текстом через запятую и другими форматами.
        """
        if not raw_text or not raw_text.strip():
            return []

        raw_text = raw_text.strip()

        try:
            products = json.loads(raw_text)
            if isinstance(products, list):
                return [p.strip() for p in products if p]
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'\[.*?\]', raw_text, re.DOTALL)
        if json_match:
            try:
                products = json.loads(json_match.group())
                if isinstance(products, list):
                    return [p.strip() for p in products if p]
            except json.JSONDecodeError:
                pass

        if ',' in raw_text:
            products = [p.strip().strip('"\'') for p in raw_text.split(',') if p.strip()]
            if products:
                return products

        if '\n' in raw_text:
            products = [p.strip().strip('"-•*') for p in raw_text.split('\n') if p.strip()]
            if products:
                return products

        return []

    @staticmethod
    def _build_client():
        return AsyncOpenAI(
            api_key=AIEngine.YANDEX_API_KEY,
            base_url=AIEngine.AI_API_URL,
            project=AIEngine.YANDEX_FOLDER_ID,
        )

    @staticmethod
    async def _client_responses_create(prompt: str, input_type: str = "input_text"):
        text = ""
        input_key = ""
        if input_type == "input_text":
            text = "Перечисли продукты/ингредиенты из текста списком. Только названия. Верни ответ в виде списка из продуктов в формате json, чтобы я в дальнейшем смог десериализовать в объект"
            input_key = "text"
        elif input_type == "input_image":
            text = "Перечисли продукты/ингредиенты на фото списком. Только названия. Верни ответ в виде списка из продуктов в формате json, чтобы я в дальнейшем смог десериализовать в объект"
            input_key = "image_url"

        client = AIEngine._build_client()
        try:
            response = await client.responses.create(
                model=AIEngine.MODEL_FOR_CV,
                temperature=0.3,
                max_output_tokens=4000,
                input=[{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": text},
                        {"type": input_type, input_key: prompt},
                    ],
                }]
            )
        except Exception as exc:
            raise AIServiceUnavailableError()

        products = AIEngine._parse_products(response.output_text)
        print(products)

        if len(products) == 0:
            raise ProductsNotFoundError()

        return products

    @staticmethod
    async def recognize_products(recognize_input: RecognizeInput) -> RecognizeResult:
        if recognize_input.img_base64 is not None:
            products = await AIEngine._client_responses_create(
                f"data:image/jpeg;base64,{base64.b64encode(recognize_input.img_base64).decode()}")
            return RecognizeResult(products=products, confidence=1.0)
        if recognize_input.text is not None:
            products = await AIEngine._client_responses_create(recognize_input.text)
            return RecognizeResult(products=products, confidence=1.0)
        raise ValueError("Invalid input")

    # TODO здесь должно выбрасываться исключение AIServiceUnavailableError в случае ошибки внешнего ИИ сервиса
    @staticmethod
    async def generate_recipes(recipes_input: RecipesInput) -> RecipesResult:
        if recipes_input.products is not None:
            client = AIEngine._build_client()
            prompt = (
                "По списку продуктов предложи 4 коротких рецепта на русском. "
                "Ответ строго JSON: {\"title\": string, \"steps\": string[]}[]. "
                f"Продукты: {', '.join(recipes_input.products)}"
            )
            try:
                response = await client.chat.completions.create(
                    model=AIEngine.MODEL_FOR_CV,
                    temperature=0.3,
                    max_tokens=1200,
                    messages=[{"role": "user", "content": prompt}],
                    reasoning_effort="none"
                )
            except Exception as exc:
                raise AIServiceUnavailableError()
            content = response.choices[0].message.content
            try:
                recipes = json.loads(content)
            except json.JSONDecodeError:
                raise AIServiceError()
            return RecipesResult(recipes=recipes, confidence=1.0)
        raise ValueError("Invalid input")

    @staticmethod
    def _mock_generate_recipes():
        return [{
            "title": "Спагетти карбонара",
            "steps": [
                "Отварить спагетти до состояния al dente.",
                "Обжарить бекон до золотистой корочки.",
                "Смешать яйца с тёртым сыром и перцем.",
                "Добавить спагетти к бекону.",
                "Снять сковороду с огня и вмешать яичную смесь.",
            ],
        },
            {
                "title": "Куриный суп",
                "steps": [
                    "Залить курицу водой и довести до кипения.",
                    "Добавить нарезанный картофель.",
                    "Обжарить лук и морковь.",
                    "Добавить овощи и лапшу в суп.",
                    "Варить до готовности и посолить.",
                ],
            },
            {
                "title": "Омлет с сыром",
                "steps": [
                    "Разбить яйца в миску.",
                    "Добавить молоко и соль.",
                    "Взбить смесь венчиком.",
                    "Вылить смесь на разогретую сковороду.",
                    "Посыпать сыром и готовить под крышкой.",
                ],
            }]

    # endregion
