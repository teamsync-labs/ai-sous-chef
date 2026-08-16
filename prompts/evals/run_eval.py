#!/usr/bin/env python3
"""
Скрипт для полуавтоматического прогона eval-кейсов.

Использование:
    python run_eval.py --case 1 --version v2
    python run_eval.py --all --version v2
"""

import json
import yaml
import argparse
from pathlib import Path
from jinja2 import Template
from typing import Dict, List, Optional

# Пути
PROMPTS_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = PROMPTS_ROOT / "fixtures"
GOLDEN_DIR = PROMPTS_ROOT / "eval" / "golden_responses"

# Фикстуры для кейсов (соответствие case_id → файл)
CASE_FIXTURES = {
    1: "simple_products.txt",
    2: "medium_products.txt",
    3: "evil_products.txt",
    4: "empty.txt",  # нужно создать
    5: "rice.txt",   # нужно создать
    6: "mixed_units.txt",  # нужно создать
    7: "drinks.txt",  # нужно создать
    8: "asian_cuisine.txt",  # нужно создать
    9: "vegan.txt",  # нужно создать
    10: "json_error.txt",  # нужно создать
}

# Ожидаемые статусы (пока ручная проверка)
# Для автоматизации можно сравнить с golden-ответами
EXPECTED_STATUS = {
    1: "ok",
    2: "ok",
    3: "ok",
    4: "error",
    5: "ok",
    6: "ok",
    7: "error",
    8: "ok",
    9: "ok",
    10: "ok",
}


def load_fixture(case_id: int) -> str:
    """Загрузить текст фикстуры для кейса."""
    filename = CASE_FIXTURES.get(case_id)
    if not filename:
        raise ValueError(f"Нет фикстуры для кейса {case_id}")
    
    filepath = FIXTURES_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Фикстура не найдена: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_prompt(prompt_type: str, version: str, variables: Dict) -> str:
    """Загрузить и скомпилировать user-промпт."""
    template_path = PROMPTS_ROOT / prompt_type / f"{version}_user.md.j2"
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    template = Template(template_str)
    return template.render(**variables)


def load_system_prompt(prompt_type: str, version: str) -> str:
    """Загрузить system-промпт."""
    system_path = PROMPTS_ROOT / prompt_type / f"{version}_system.md"
    with open(system_path, "r", encoding="utf-8") as f:
        return f.read()


def load_config(prompt_type: str, version: str) -> Dict:
    """Загрузить конфиг."""
    config_path = PROMPTS_ROOT / prompt_type / f"{version}_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def call_llm(prompt_type: str, version: str, input_text: str, extra_vars: Optional[Dict] = None) -> str:
    """
    Эмуляция вызова LLM (заглушка).
    Реальный вызов нужно заменить на YandexGPT API.
    """
    variables = {"products_text": input_text, "products": input_text}
    if extra_vars:
        variables.update(extra_vars)
    
    system = load_system_prompt(prompt_type, version)
    user = load_prompt(prompt_type, version, variables)
    config = load_config(prompt_type, version)
    
    # 🔥 Здесь ваш вызов YandexGPT
    print(f"[LLM] Model: {config['model']}, Temperature: {config['temperature']}")
    print(f"[LLM] System: {system[:100]}...")
    print(f"[LLM] User: {user[:100]}...")
    
    # Заглушка: возвращаем текст из golden-ответа
    # В реальном коде — вызов API
    return '{"status": "ok", "recipes": []}'


def validate_json(response: str) -> tuple[bool, dict]:
    """Проверка валидности JSON."""
    try:
        data = json.loads(response)
        return True, data
    except json.JSONDecodeError:
        return False, {}


def check_products_from_air(products_input: List[str], recipe_data: Dict) -> bool:
    """
    Проверка: есть ли продукты "из воздуха" (которые не были во входе).
    Сложная проверка — упрощённый вариант.
    """
    # Это упрощённая эвристика, в реальности нужно делать семантический анализ
    input_set = set(p.lower() for p in products_input)
    for recipe in recipe_data.get("recipes", []):
        for missing in recipe.get("missing_products", []):
            if missing["name"].lower() not in input_set:
                return True
    return False


def run_eval(case_id: int, version: str, prompt_type: str = "recipes_with_normalize"):
    """Запустить eval для одного кейса."""
    print(f"\n{'='*60}")
    print(f"Кейс {case_id} | Версия {version} | {prompt_type}")
    print(f"{'='*60}")
    
    # Загрузка входных данных
    input_text = load_fixture(case_id)
    print(f"Вход: {input_text[:100]}...")
    
    # Дополнительные переменные (для cuisine/diet)
    extra_vars = {}
    if case_id == 8:
        extra_vars["cuisine"] = "asian"
    if case_id == 9:
        extra_vars["diet"] = "vegan"
    
    # Вызов LLM
    response = call_llm(prompt_type, version, input_text, extra_vars)
    print(f"Ответ: {response[:200]}...")
    
    # Проверка валидности JSON
    is_valid, data = validate_json(response)
    print(f"✅ JSON валидный: {is_valid}")
    
    # Если JSON невалидный — сразу fail
    if not is_valid:
        return {"case": case_id, "status": "fail", "reason": "invalid JSON"}
    
    # Проверка "продуктов из воздуха"
    # (упрощённо: разбиваем вход на слова)
    input_words = input_text.lower().split()
    has_air_products = check_products_from_air(input_words, data)
    print(f"✅ Продукты 'из воздуха': {has_air_products}")
    
    # Проверка шагов без опоры
    has_vague_steps = False
    for recipe in data.get("recipes", []):
        for step in recipe.get("steps", []):
            vague_phrases = ["до готовности", "пока не приготовится", "до мягкости"]
            if any(phrase in step.lower() for phrase in vague_phrases):
                has_vague_steps = True
                break
    print(f"✅ Шаги без опоры: {has_vague_steps}")
    
    # Итоговый вердикт
    is_ok = is_valid and not has_air_products and not has_vague_steps
    status = "ok" if is_ok else "fail"
    
    # Сравнение с ожидаемым статусом (для автоматизации)
    expected = EXPECTED_STATUS.get(case_id, "ok")
    print(f"Ожидаемый статус: {expected}, Получен: {status}")
    print(f"✅ ИТОГ: {status}")
    
    return {
        "case": case_id,
        "status": status,
        "expected": expected,
        "is_valid": is_valid,
        "has_air_products": has_air_products,
        "has_vague_steps": has_vague_steps,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, help="Номер кейса (1–10)")
    parser.add_argument("--all", action="store_true", help="Прогнать все кейсы")
    parser.add_argument("--version", default="v2", help="Версия промпта (v1, v2)")
    parser.add_argument("--type", default="recipes_with_normalize", help="Тип промпта")
    args = parser.parse_args()
    
    if args.all:
        results = []
        for case_id in range(1, 11):
            result = run_eval(case_id, args.version, args.type)
            results.append(result)
        
        # Итоговая статистика
        total = len(results)
        ok_count = sum(1 for r in results if r["status"] == "ok")
        fail_count = total - ok_count
        print(f"\n{'='*60}")
        print(f"ИТОГО: {ok_count}/{total} OK ({ok_count/total*100:.0f}%)")
        print(f"{'='*60}")
    else:
        if args.case is None:
            print("Укажите --case N или --all")
            return
        run_eval(args.case, args.version, args.type)


if __name__ == "__main__":
    main()