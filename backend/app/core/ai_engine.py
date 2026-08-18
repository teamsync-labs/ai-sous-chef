import base64
import json
import re

from app.api.api_models import RecipesResult, RecognizeResult, RecipesInput, RecognizeInput
from abc import ABC, abstractmethod

from app.core.config import settings
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from openai.types.responses import EasyInputMessageParam, ResponseInputTextParam, ResponseInputImageParam
from openai.types.shared_params import ResponseFormatJSONObject


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
    async def _client_responses_create(
            prompt: str,
            input_type: str = "input_text",
    ):
        system_prompt = """
        Ты AI-помощник по нормализации продуктов.
    
        Твоя задача:
        преобразовать сырой список/подписи с фото в короткий список названий продуктов на русском языке.
    
        Правила:
        - оставь только названия продуктов (например: «яйца», «молоко», «сыр»);
        - удали дубликаты;
        - удали бренды, марки, магазины;
        - удали мусорные слова: «упаковка», «стол», «фон», «на фото», «рядом», «лежит» и т. п.;
        - не добавляй продукты, которых нет в исходнике;
        - не придумывай категории или описания;
        - язык: русский;
        - ответь ТОЛЬКО валидным JSON без markdown‑обёрток (никаких ```json);
        - игнорируй стоп-слова («купи», «срочно», «хочется»);
        - если количество не указано, используй null;
        - валидные единицы измерения: шт, кг, г, л, мл;
        - лимит ответа ~500–800 токенов
    
        Формат ответа:
        {"products":["название1","название2","название3"],"confidence":0.0-1.0}
        
        Пример того, что модель должна вернуть (после вызова LLM)
        {"products":["яйца","молоко","сыр"],"confidence":1}
        """

        user_prompt = """
        Извлеки продукты из текста и верни JSON по схеме:
        {"products": [{"name": "string", "quantity": "number or null", "unit": "string or null"}]}
        
        Пример правильного ответа:
        Вход: "яйца 10 шт, молоко и хлеб"
        Выход: {"products": [{"name": "яйцо", "quantity": 10, "unit": "шт"}, 
        {"name": "молоко", "quantity": null, "unit": null}, 
        {"name": "хлеб", "quantity": null, "unit": null}]}
        
        Поле confidence:
        - 1.0 — если все продукты однозначно распознаны;
        - 0.5–0.9 — если есть сомнения в названии или неоднозначность;
        - <0.5 — если входной текст почти нечитаем или содержит только мусор.
    
        Входные данные:
        """

        if input_type == "input_text":
            user_message = EasyInputMessageParam(
                role="user",
                content=[
                    ResponseInputTextParam(
                        type="input_text",
                        text=user_prompt + prompt,
                    )
                ],
            )

        elif input_type == "input_image":
            user_message = EasyInputMessageParam(
                role="user",
                content=[
                    ResponseInputTextParam(
                        type="input_text",
                        text=user_prompt,
                    ),
                    ResponseInputImageParam(
                        type="input_image",
                        image_url=prompt,
                    ),
                ],
            )

        else:
            raise ValueError(
                f"Unsupported input_type: {input_type}"
            )

        client = AIEngine._build_client()
        try:
            response = await client.responses.create(
                model=AIEngine.MODEL_FOR_CV,
                instructions=system_prompt,
                input=[user_message],
                temperature=0.3,
                max_output_tokens=4000,
            )

        except Exception as exc:
            raise AIServiceUnavailableError() from exc

        try:
            output = response.output_text.strip()
            data = json.loads(output)
            result = RecognizeResult(
                products=[
                    product["name"]
                    for product in data["products"]
                ],
                confidence=data["confidence"],
            )

        except Exception as exc:
            raise ProductsNotFoundError() from exc

        if not result.products:
            raise ProductsNotFoundError()

        return result.products

    @staticmethod
    async def recognize_products(recognize_input: RecognizeInput) -> RecognizeResult:
        if recognize_input.img_base64 is not None:
            products = await AIEngine._client_responses_create(
                f"data:image/jpeg;base64,{base64.b64encode(recognize_input.img_base64).decode()}",
                input_type="input_image")
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
            system_prompt = (
                f"Ты — помощник на кухне AI Sous-Chef. По списку продуктов: {', '.join(recipes_input.products)} "
                "предложи 2–3 простых рецепта. Правила:\n"
                "- используй в основном переданные продукты;\n"
                "- если добавляешь базу (соль, масло, вода) — укажи это явно;\n"
                "- не выдумывай редкие ингредиенты, которых нет в списке;\n"
                "- шаги конкретные: время, температура или визуальный признак готовности;\n"
                "- язык: русский;\n"
                r"- ответь ТОЛЬКО валидным JSON без markdown-обёрток (никаких ```json);\n"
                "- лимит ответа ~1200–1500 токенов"
            )

            user_message = (
                "Верни ответ в формате:\n"
                "{\n"
                '  "recipes": [\n'
                "    {\n"
                '      "title": "Название рецепта",\n'
                '      "steps": ["Шаг 1", "Шаг 2", "Шаг 3"]\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "Требования:\n"
                "- строго валидный JSON\n"
                "- без markdown-обёрток\n"
                "- лимит ответа: ~1200–1500 токенов\n"
                "- каждый шаг — конкретное действие с параметром готовности"
            )
            try:
                response = await client.chat.completions.create(
                    model=AIEngine.MODEL_FOR_CV,
                    temperature=0.3,
                    max_tokens=1200,
                    messages=[
                        ChatCompletionSystemMessageParam(role="system", content=system_prompt),
                        ChatCompletionUserMessageParam(role="user", content=user_message)
                    ],
                    reasoning_effort="none",
                    response_format=ResponseFormatJSONObject(type="json_object")
                )
            except Exception as exc:
                raise AIServiceUnavailableError()
            content = response.choices[0].message.content
            try:
                recipes = json.loads(content)
            except json.JSONDecodeError:
                raise AIServiceError()
            return RecipesResult(recipes=recipes.get("recipes", []), confidence=1.0)
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
