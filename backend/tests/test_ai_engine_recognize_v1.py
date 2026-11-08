"""
V1 recognize: модель иногда отдаёт products как объекты {name, quantity, unit}
вместо list[str]. AIEngineV1 должен нормализовать к RecognizeResult.products: list[str].
"""

from app.core.ai_engine import AIEngineV1


class TestAIEngineV1BuildRecognizeResult:
    def test_accepts_string_products(self):
        result = AIEngineV1._build_recognize_result(
            {"products": ["молоко", "яйца", "хлеб"], "confidence": 0.9}
        )
        assert result.products == ["молоко", "яйца", "хлеб"]
        assert result.confidence == 0.9

    def test_accepts_object_products_with_name(self):
        result = AIEngineV1._build_recognize_result(
            {
                "products": [
                    {"name": "молоко", "quantity": None, "unit": None},
                    {"name": "яйца", "quantity": 10, "unit": "шт"},
                    {"name": "хлеб", "quantity": None, "unit": None},
                ],
                "confidence": 1.0,
            }
        )
        assert result.products == ["молоко", "яйца", "хлеб"]
        assert result.confidence == 1.0

    def test_accepts_mixed_string_and_object_products(self):
        result = AIEngineV1._build_recognize_result(
            {
                "products": [
                    "рис",
                    {"name": "картошка", "quantity": 1, "unit": "кг"},
                ],
                "confidence": 0.5,
            }
        )
        assert result.products == ["рис", "картошка"]
