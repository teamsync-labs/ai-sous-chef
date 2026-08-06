import logging
from typing import Callable

from fastapi import APIRouter, HTTPException, status

from .api_models import RecipesInput, RecipesResult, RecognizeInput, RecognizeResult, BaseAPIModel
from app.core.ai_engine import AIEngine, AIServiceUnavailableError, ProductsNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/app/api",
    tags=["MVP API"]
)


async def proceed_ai(
        operation: str,
        ai_method: Callable[[], BaseAPIModel],
) -> BaseAPIModel:
    try:
        return ai_method()

    except ValueError as exc:
        logger.warning(
            "AI request rejected: operation=%s reason=%s",
            operation,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing_input",
        ) from exc

    except AIServiceUnavailableError as exc:
        logger.error(
            "AI service unavailable: operation=%s reason=%s",
            operation,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ai_service_error",
        ) from exc
    except ProductsNotFoundError as exc:
        logger.warning(
            "Products not found: operation=%s reason=%s",
            operation,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="no_products_found",
        ) from exc
    except Exception:
        logger.exception("Unexpected API error: operation=%s", operation)
        raise


# OPTIMIZE: использовать асинхронные вызовы в ai_engine чтобы async def имело смысл

@router.post(
    "/recognize",
    response_model=RecognizeResult,
    summary="Распознать продукты",
    description=(
            "Распознаёт продукты по переданному изображению или текстовому описанию. "
            "Если передано изображение, продукты сначала определяются CV-моделью. "
            "Затем результат обрабатывается языковой моделью и преобразуется "
            "в нормализованный список продуктов.\n"
            "Возвращает список распознанных продуктов и уверенность модели. **Передавать только либо base_64, либо text**"))
async def recognize(recognize_input: RecognizeInput):
    return await proceed_ai(
        "recognize",
        lambda: AIEngine.recognize_products(recognize_input),
    )


@router.post(
    "/recipes",
    response_model=RecipesResult,
    summary="Сгенерировать рецепты",
    description=(
            "Генерирует рецепты на основе переданного списка продуктов. "
            "Предполагается, что пользователь предварительно проверил и подтвердил "
            "список продуктов, полученный через эндпоинт `/recognize`.\n"
            "Возвращает список рецептов. Каждый рецепт содержит название "
            "и последовательность шагов приготовления."
    ))
async def recipes(recipes_input: RecipesInput):
    return await proceed_ai(
        "recipes",
        lambda: AIEngine.generate_recipes(recipes_input),
    )
