"""Загрузка pin и промптов из prompts/ (без вызова LLM)."""

from app.core.prompts_loader import clear_prompt_cache, load_pin, load_prompt_pair


def setup_function():
    clear_prompt_cache()


def teardown_function():
    clear_prompt_cache()


def test_pin_has_recognize_and_recipes():
    pin = load_pin()
    assert pin["recognize"] == "v1"
    assert pin["recipes"] == "v1"


def test_load_recognize_prompt_substitutes_input():
    version, system, user = load_prompt_pair("recognize", input="яйца, молоко")
    assert version == "v1"
    assert "нормализации продуктов" in system
    assert "яйца, молоко" in user
    assert "{{ input }}" not in user


def test_load_recipes_prompt_substitutes_products():
    version, system, user = load_prompt_pair("recipes", products="яйца, молоко")
    assert version == "v1"
    assert "яйца, молоко" in system
    assert "{{ products }}" not in system
    assert "recipes" in user
