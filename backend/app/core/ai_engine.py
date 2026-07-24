from app.api.api_models import RecipesResult, RecognizeResult, RecipesInput, RecognizeInput
from abc import ABC, abstractmethod

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
    @staticmethod
    def recognize_products(recognize_input: RecognizeInput) -> RecognizeResult:
        if recognize_input.img_base64 is not None:
            return RecognizeResult(products=["base64 input"], confidence=1.0)
        if recognize_input.text is not None:
            return RecognizeResult(products=["text input"], confidence=1.0)
        raise ValueError("Invalid input")

    # TODO здесь должно выбрасываться исключение AIServiceUnavailableError в случае ошибки внешнего ИИ сервиса
    @staticmethod
    def generate_recipes(recipes_input: RecipesInput) -> RecipesResult:
        if recipes_input.products is not None:
            return RecipesResult(recipes=AIEngine._mock_generate_recipes())
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