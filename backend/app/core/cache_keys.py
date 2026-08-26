"""
Хелпер для нормализации списка продуктов и построения ключей кэша.

Стратегия кэширования описана в docs/redis-cache.md
"""

from typing import List
import re


def normalize_ingredients(ingredients: List[str]) -> List[str]:
    """
    Нормализует список продуктов по правилам из redis-cache.md:
    1. Все названия в lowercase
    2. Trim пробелов по краям
    3. Множественные пробелы сведены к одному
    4. Удаление дубликатов
    5. Сортировка по алфавиту

    Args:
        ingredients: Список названий продуктов

    Returns:
        Нормализованный отсортированный список уникальных продуктов

    Examples:
        >>> normalize_ingredients(["  Apple  ", "BANANA", "apple", "carrot  "])
        ["apple", "banana", "carrot"]

        >>> normalize_ingredients(["milk", "  Flour  ", "sugar", "flour"])
        ["flour", "milk", "sugar"]
    """
    if not ingredients:
        return []

    normalized = []
    for item in ingredients:
        if not item or not isinstance(item, str):
            continue

        # Приводим к lowercase
        processed = item.lower().strip()

        # Схлопываем множественные пробелы в один
        processed = re.sub(r'\s+', ' ', processed)

        # Пропускаем пустые строки
        if processed:
            normalized.append(processed)

    # Удаляем дубликаты и сортируем
    return sorted(list(set(normalized)))


def build_recipe_cache_key(
    ingredients: List[str],
    model_name: str = "yandex-global",
    prompt_version: str = "recipes_v1",
    cache_version: str = "v1"
) -> str:
    """
    Строит ключ кэша для /api/recipes по спецификации из docs/redis-cache.md

    Формат: ai-cache:{cache_version}:recipes:model={model_name}:prompt={prompt_version}:products={normalized_products}

    Args:
        ingredients: Список продуктов
        model_name: Имя модели (по умолчанию "yandex-global")
        prompt_version: Версия промпта (по умолчанию "recipes_v1")
        cache_version: Версия кэша (по умолчанию "v1")

    Returns:
        Строка ключа кэша

    Examples:
        >>> build_recipe_cache_key(["Apple", "banana", "Carrot"])
        "ai-cache:v1:recipes:model=yandex-global:prompt=recipes_v1:products=apple,banana,carrot"

        >>> build_recipe_cache_key(["  Milk  ", "Flour", "milk"], model_name="gpt-4o-mini")
        "ai-cache:v1:recipes:model=gpt-4o-mini:prompt=recipes_v1:products=flour,milk"
    """
    normalized = normalize_ingredients(ingredients)
    products_str = ",".join(normalized)

    return f"ai-cache:{cache_version}:recipes:model={model_name}:prompt={prompt_version}:products={products_str}"