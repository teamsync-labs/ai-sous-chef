"""
Автотесты для endpoint'ов recognize и recipes.
Не требуют Redis и реального LLM.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.api_models import RecognizeResult, RecipesResult
from app.main import app

# Создаем клиент для тестов
client = TestClient(app)

# Готовые ответы «как будто вернул LLM» — без сети и ключей.
_MOCK_RECOGNIZE = RecognizeResult(
    products=["chicken", "rice", "onion"],
    confidence=0.9,
)
_MOCK_RECIPES = RecipesResult(
    recipes=[{"title": "Test recipe", "steps": ["Step 1", "Step 2"]}],
)


@pytest.fixture
def mock_ai_engine():
    """Подменяем AIEngine в api.py: proceed_ai не ходит во внешний API."""
    with (
        patch(
            "app.api.api.AIEngine.recognize_products",
            new_callable=AsyncMock,
            return_value=_MOCK_RECOGNIZE,
        ),
        patch(
            "app.api.api.AIEngine.generate_recipes",
            new_callable=AsyncMock,
            return_value=_MOCK_RECIPES,
        ),
    ):
        yield


# ============================================
# Тесты для эндпоинта /recognize
# ============================================

class TestRecognizeEndpoint:
    """Тесты для POST /app/api/recognize."""

    def test_recognize_with_text_success(self, mock_ai_engine):
        """Тест: успешное распознавание продуктов по тексту."""
        response = client.post(
            "/app/api/recognize",
            json={"text": "chicken, rice, onion"}
        )
        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру ответа
        assert "products" in data
        assert "confidence" in data
        assert isinstance(data["products"], list)
        assert isinstance(data["confidence"], float)

        # Проверяем, что продукты не пустые
        assert len(data["products"]) > 0
        assert data["confidence"] >= 0.0 and data["confidence"] <= 1.0

    def test_recognize_missing_input(self):
        """Тест: ошибка при отсутствии входа (нет text и нет img_base64)."""
        response = client.post(
            "/app/api/recognize",
            json={}  # Пустой запрос
        )
        # API должен вернуть 400 или 422
        assert response.status_code in [400, 422]

        # Проверяем, что есть сообщение об ошибке
        data = response.json()
        assert "detail" in data

    def test_recognize_with_both_fields(self):
        """Тест: ошибка при передаче обоих полей (text и img_base64)."""
        response = client.post(
            "/app/api/recognize",
            json={
                "text": "chicken",
                "img_base64": "dummy_data"
            }
        )
        # API должен вернуть 400 или 422
        assert response.status_code in [400, 422]
        data = response.json()
        assert "detail" in data


# ============================================
# Тесты для эндпоинта /recipes
# ============================================

class TestRecipesEndpoint:
    """Тесты для POST /app/api/recipes."""

    def test_recipes_with_products_success(self, mock_ai_engine):
        """Тест: успешная генерация рецептов по продуктам."""
        response = client.post(
            "/app/api/recipes",
            json={"products": ["chicken", "rice", "onion"]}
        )
        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру ответа
        assert "recipes" in data
        assert isinstance(data["recipes"], list)
        assert len(data["recipes"]) > 0

        # Проверяем структуру первого рецепта
        first_recipe = data["recipes"][0]
        assert "title" in first_recipe
        assert "steps" in first_recipe
        assert isinstance(first_recipe["steps"], list)
        assert len(first_recipe["steps"]) > 0

    def test_recipes_missing_products(self):
        """Тест: ошибка при отсутствии поля products."""
        response = client.post(
            "/app/api/recipes",
            json={}  # Пустой запрос
        )
        assert response.status_code in [400, 422]
        data = response.json()
        assert "detail" in data

    def test_recipes_invalid_products_type(self):
        """Тест: ошибка при неверном типе products (число вместо списка)."""
        response = client.post(
            "/app/api/recipes",
            json={"products": 123}
        )
        # FastAPI вернет 422 при валидации модели
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ============================================
# Проверка структуры ответов
# ============================================

def test_recognize_response_structure(mock_ai_engine):
    """Тест: проверка структуры ответа recognize."""
    response = client.post(
        "/app/api/recognize",
        json={"text": "chicken, rice"}
    )
    assert response.status_code == 200
    data = response.json()

    # Проверяем наличие всех полей
    expected_fields = {"products", "confidence"}
    assert expected_fields.issubset(data.keys())

    # Проверяем типы
    assert isinstance(data["products"], list)
    assert all(isinstance(p, str) for p in data["products"])
    assert isinstance(data["confidence"], float)


def test_recipes_response_structure(mock_ai_engine):
    """Тест: проверка структуры ответа recipes."""
    response = client.post(
        "/app/api/recipes",
        json={"products": ["chicken", "rice"]}
    )
    assert response.status_code == 200
    data = response.json()

    # Проверяем наличие поля recipes
    assert "recipes" in data
    assert isinstance(data["recipes"], list)

    # Проверяем структуру каждого рецепта
    for recipe in data["recipes"]:
        assert "title" in recipe
        assert "steps" in recipe
        assert isinstance(recipe["steps"], list)
