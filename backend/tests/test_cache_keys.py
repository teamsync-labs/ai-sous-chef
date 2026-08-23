"""
Unit-тесты для хелпера нормализации продуктов (cache_keys.py)
"""

import pytest
from app.core.cache_keys import normalize_ingredients, build_recipe_cache_key


class TestNormalizeIngredients:
    """Тесты для normalize_ingredients"""

    def test_lowercase_conversion(self):
        """Проверка приведения к lowercase"""
        result = normalize_ingredients(["Apple", "BANANA", "Carrot"])
        assert result == ["apple", "banana", "carrot"]

    def test_trim_spaces(self):
        """Проверка удаления пробелов по краям"""
        result = normalize_ingredients(["  apple  ", " banana ", "carrot  "])
        assert result == ["apple", "banana", "carrot"]

    def test_collapse_multiple_spaces(self):
        """Проверка схлопывания множественных пробелов"""
        result = normalize_ingredients(["apple   juice", "banana  milk", "carrot  cake"])
        assert result == ["apple juice", "banana milk", "carrot cake"]

    def test_remove_duplicates(self):
        """Проверка удаления дубликатов"""
        result = normalize_ingredients(["apple", "banana", "apple", "carrot", "banana"])
        assert result == ["apple", "banana", "carrot"]

    def test_sorting(self):
        """Проверка сортировки по алфавиту"""
        result = normalize_ingredients(["zucchini", "apple", "banana", "carrot"])
        assert result == ["apple", "banana", "carrot", "zucchini"]

    def test_empty_list(self):
        """Проверка пустого списка"""
        result = normalize_ingredients([])
        assert result == []

    def test_empty_strings(self):
        """Проверка пустых строк"""
        result = normalize_ingredients(["", "apple", "  ", "banana"])
        assert result == ["apple", "banana"]

    def test_mixed_case_and_spaces(self):
        """Проверка смешанного регистра и пробелов"""
        result = normalize_ingredients(["  APPLE  ", "banana", "  CARROT   juice  "])
        assert result == ["apple", "banana", "carrot juice"]


class TestBuildRecipeCacheKey:
    """Тесты для build_recipe_cache_key"""

    def test_same_ingredients_different_order(self):
        """Одинаковые продукты в разном порядке → один ключ"""
        key1 = build_recipe_cache_key(["apple", "banana", "carrot"])
        key2 = build_recipe_cache_key(["carrot", "apple", "banana"])
        key3 = build_recipe_cache_key(["banana", "carrot", "apple"])
        assert key1 == key2 == key3

    def test_same_ingredients_different_case(self):
        """Одинаковые продукты в разном регистре → один ключ"""
        key1 = build_recipe_cache_key(["apple", "banana", "carrot"])
        key2 = build_recipe_cache_key(["APPLE", "BANANA", "CARROT"])
        key3 = build_recipe_cache_key(["Apple", "Banana", "Carrot"])
        assert key1 == key2 == key3

    def test_same_ingredients_with_spaces(self):
        """Одинаковые продукты с разными пробелами → один ключ"""
        key1 = build_recipe_cache_key(["apple", "banana", "carrot"])
        key2 = build_recipe_cache_key(["  apple  ", "banana", "carrot  "])
        key3 = build_recipe_cache_key(["apple", "banana", "carrot  "])
        assert key1 == key2 == key3

    def test_different_ingredients(self):
        """Разные наборы продуктов → разные ключи"""
        key1 = build_recipe_cache_key(["apple", "banana", "carrot"])
        key2 = build_recipe_cache_key(["apple", "banana", "orange"])
        key3 = build_recipe_cache_key(["apple", "banana"])
        assert key1 != key2 != key3

    def test_duplicates_removed(self):
        """Дубликаты не влияют на ключ"""
        key1 = build_recipe_cache_key(["apple", "banana", "carrot"])
        key2 = build_recipe_cache_key(["apple", "banana", "apple", "carrot", "banana"])
        assert key1 == key2

    def test_key_format(self):
        """Проверка формата ключа согласно документации"""
        key = build_recipe_cache_key(["apple", "banana"])
        expected = "ai-cache:v1:recipes:model=yandex-global:prompt=recipes_v1:products=apple,banana"
        assert key == expected

    def test_custom_params(self):
        """Проверка кастомных параметров"""
        key = build_recipe_cache_key(
            ["apple", "banana"],
            model_name="gpt-4o-mini",
            prompt_version="recipes_v2",
            cache_version="v2"
        )
        expected = "ai-cache:v2:recipes:model=gpt-4o-mini:prompt=recipes_v2:products=apple,banana"
        assert key == expected