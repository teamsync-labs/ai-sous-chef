import base64
import json
import logging
import re
from abc import ABC, abstractmethod
from openai import AsyncOpenAI, OpenAIError

from ..api.api_models import RecipesResult, RecognizeResult, RecipesInput, RecognizeInput

from ..core.config import settings
from ..core.prompts_loader import load_prompt_pair
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from openai.types.responses import EasyInputMessageParam, ResponseInputTextParam, ResponseInputImageParam
from openai.types.shared_params import ResponseFormatJSONObject

logger = logging.getLogger(__name__)


class AIServiceError(RuntimeError):
    pass


class AIServiceUnavailableError(AIServiceError):
    pass


class ProductsNotFoundError(AIServiceError):
    pass


class AIProtocol(ABC):
    @staticmethod
    @abstractmethod
    async def recognize_products(recognize_input: RecognizeInput) -> RecognizeResult:
        pass

    @staticmethod
    @abstractmethod
    async def generate_recipes(recipes_input: RecipesInput) -> RecipesResult:
        pass


def get_ai_engine():
    logger.info("AI Mode = %s", settings.AI_MODE)
    if settings.AI_MODE == "stub":
        return AIEngineStub
    return AIEngine


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
            logger.debug("Response is not valid JSON, trying delimited parsing")
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
        try:
            client = AsyncOpenAI(
                api_key=AIEngine.YANDEX_API_KEY,
                base_url=AIEngine.AI_API_URL,
                project=AIEngine.YANDEX_FOLDER_ID,
            )
        except OpenAIError as exc:
            logger.error("Failed to build OpenAI client (OpenAIError): %s", exc, exc_info=True)
            raise AIServiceUnavailableError(exc) from exc
        except Exception as exc:
            logger.error("Failed to build OpenAI client: %s", exc, exc_info=True)
            raise AIServiceUnavailableError(exc) from exc
        return client

    @staticmethod
    async def _client_responses_create(
            prompt: str,
            input_type: str = "input_text",
    ):
        version, system_prompt, user_prompt = load_prompt_pair(
            "recognize",
            input=prompt if input_type == "input_text" else "",
        )

        if input_type == "input_text":
            user_message = EasyInputMessageParam(
                role="user",
                content=[
                    ResponseInputTextParam(
                        type="input_text",
                        text=user_prompt,
                    )
                ],
            )

        elif input_type == "input_image":
            # Для фото вход в user.md пустой ({{ input }} → ""); картинка отдельным блоком.
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
            logger.info(
                "CV request: model=%s prompt=recognize/%s input_type=%s",
                AIEngine.MODEL_FOR_CV,
                version,
                input_type,
            )
            response = await client.responses.create(
                model=AIEngine.MODEL_FOR_CV,
                instructions=system_prompt,
                input=[user_message],
                temperature=0.3,
                max_output_tokens=4000,
            )

        except Exception as exc:
            logger.error("CV request failed: model=%s input_type=%s: %s", AIEngine.MODEL_FOR_CV, input_type, exc,
                         exc_info=True)
            raise AIServiceUnavailableError(exc) from exc

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
            logger.warning("No products in CV response: input_type=%s", input_type)
            raise ProductsNotFoundError() from exc

        if not result.products:
            logger.warning("No products in CV response: input_type=%s", input_type)
            raise ProductsNotFoundError()

        return result.products

    @staticmethod
    async def recognize_products(recognize_input: RecognizeInput) -> RecognizeResult:
        if recognize_input.img_base64 is not None:
            logger.info("Recognize request: input_type=image img_bytes=%d", len(recognize_input.img_base64))
            products = await AIEngine._client_responses_create(
                f"data:image/jpeg;base64,{base64.b64encode(recognize_input.img_base64).decode()}",
                input_type="input_image")
            logger.info("Products recognized from image: count=%d", len(products))
            return RecognizeResult(products=products, confidence=1.0)
        if recognize_input.text is not None:
            logger.info("Recognize request: input_type=text text_len=%d", len(recognize_input.text))
            products = await AIEngine._client_responses_create(recognize_input.text)
            logger.info("Products recognized from text: count=%d", len(products))
            return RecognizeResult(products=products, confidence=1.0)
        logger.warning("Invalid recognize input: neither image nor text provided")
        raise ValueError("Invalid input")

    # TODO здесь должно выбрасываться исключение AIServiceUnavailableError в случае ошибки внешнего ИИ сервиса
    @staticmethod
    async def generate_recipes(recipes_input: RecipesInput) -> RecipesResult:
        if recipes_input.products is not None:
            client = AIEngine._build_client()
            version, system_prompt, user_message = load_prompt_pair(
                "recipes",
                products=", ".join(recipes_input.products),
            )
            try:
                logger.info(
                    "LLM request: model=%s prompt=recipes/%s products=%d",
                    AIEngine.MODEL_FOR_LLM,
                    version,
                    len(recipes_input.products),
                )
                response = await client.chat.completions.create(
                    model=AIEngine.MODEL_FOR_LLM,
                    temperature=0.3,
                    max_tokens=1200,
                    messages=[
                        ChatCompletionSystemMessageParam(role="system", content=system_prompt),
                        ChatCompletionUserMessageParam(role="user", content=user_message)
                    ],
                    reasoning_effort="none",
                    response_format=ResponseFormatJSONObject(type="json_object")
                )
                logger.info("Recipes generated by LLM model: model=%s prompt=recipes/%s", AIEngine.MODEL_FOR_LLM, version)
            except Exception as exc:
                logger.error("LLM request failed: model=%s: %s", AIEngine.MODEL_FOR_LLM, exc, exc_info=True)
                raise AIServiceUnavailableError(exc) from exc
            content = response.choices[0].message.content
            try:
                recipes = json.loads(content)
            except json.JSONDecodeError as exc:
                logger.error("Failed to parse recipes JSON (%s) from model response: %s", content, exc)
                raise AIServiceError(exc) from exc
            logger.info("Recipes parsed successfully: count=%d", len(recipes.get("recipes", [])))
            return RecipesResult(recipes=recipes.get("recipes", []))
        logger.warning("Invalid recipes input: products is None")
        raise ValueError("Invalid input")


class AIEngineStub(AIProtocol):
    @staticmethod
    async def recognize_products(recognize_input: RecognizeInput) -> RecognizeResult:
        if recognize_input.img_base64 is not None:
            return RecognizeResult(products=["base64 input"], confidence=1.0)
        if recognize_input.text is not None:
            return RecognizeResult(products=["text input"], confidence=1.0)
        raise ValueError("Invalid input")

    @staticmethod
    async def generate_recipes(recipes_input: RecipesInput) -> RecipesResult:
        if recipes_input.products is not None:
            return RecipesResult(recipes=AIEngineStub._mock_generate_recipes())
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
