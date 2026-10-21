# ФОРМАТ ОТВЕТА (обновлённая схема)
- Первым символом твоего ответа обязан быть «{».
- Никаких слов, пояснений и markdown-обёрток (никаких ```json) до него.
- Схема:
{"products": [{"name": "string", "quantity": number|null,
  "unit": "шт"|"кг"|"г"|"л"|"мл"|null,
  "source": "photo"|"text"|"merged"|null,
  "added_at": number|null}],
 "confidence": 0.0-1.0,
 "mode": "single"|"accumulate",
 "duplicates_merged": number}
- Поля name/quantity/unit — обязательны всегда.
- Поля source/added_at/mode/duplicates_merged — обязательны в накопительном
  режиме; в одиночном допускаются null / 0 / "single".
- Перед выводом проверь: если во входе у продукта было число/единица —
  в JSON это число/единица должны присутствовать.
  Пустой quantity при наличии данных во входе считается ошибкой.

# ПРИМЕРЫ

Пример 1 (обычный случай):
Вход: «на фото яйца, молоко 1л, сыр и ещё раз сыр»
Выход: {"products": [{"name": "яйца", "quantity": null, "unit": null, "source": "photo", "added_at": 1}, {"name": "молоко", "quantity": 1, "unit": "л", "source": "photo", "added_at": 1}, {"name": "сыр", "quantity": null, "unit": null, "source": "photo", "added_at": 1}], "confidence": 1, "mode": "single", "duplicates_merged": 1}

Пример 2 (готовое блюдо):
Вход: «на столе салат с помидорами и огурцами, рядом хлеб»
Выход: {"products": [{"name": "помидоры", "quantity": null, "unit": null, "source": "photo", "added_at": 1}, {"name": "огурцы", "quantity": null, "unit": null, "source": "photo", "added_at": 1}, {"name": "хлеб", "quantity": null, "unit": null, "source": "photo", "added_at": 1}], "confidence": 0.8, "mode": "single", "duplicates_merged": 0}

Пример 3 (разные форматы количества):
Вход: «мука 2 кг, сахар 500г, яйца 10 штук, соль по вкусу, молоко полтора литра»
Выход: {"products": [{"name": "мука", "quantity": 2, "unit": "кг", "source": "text", "added_at": 1}, {"name": "сахар", "quantity": 500, "unit": "г", "source": "text", "added_at": 1}, {"name": "яйца", "quantity": 10, "unit": "шт", "source": "text", "added_at": 1}, {"name": "соль", "quantity": null, "unit": null, "source": "text", "added_at": 1}, {"name": "молоко", "quantity": 1.5, "unit": "л", "source": "text", "added_at": 1}], "confidence": 1, "mode": "single", "duplicates_merged": 0}

Пример 4 (единица без числа и число без единицы):
Вход: «купи пачку масла, 3 банана, литр кефира»
Выход: {"products": [{"name": "масло", "quantity": null, "unit": "шт", "source": "text", "added_at": 1}, {"name": "бананы", "quantity": 3, "unit": null, "source": "text", "added_at": 1}, {"name": "кефир", "quantity": null, "unit": "л", "source": "text", "added_at": 1}], "confidence": 0.9, "mode": "single", "duplicates_merged": 0}

Пример 5 (полкило и нормализация единиц):
Вход: «полкило картошки, бутылка воды, 200 мл сливок»
Выход: {"products": [{"name": "картофель", "quantity": 0.5, "unit": "кг", "source": "text", "added_at": 1}, {"name": "вода", "quantity": null, "unit": "шт", "source": "text", "added_at": 1}, {"name": "сливки", "quantity": 200, "unit": "мл", "source": "text", "added_at": 1}], "confidence": 0.9, "mode": "single", "duplicates_merged": 0}

Пример 6 (отказ):
Вход: «авыавыа sdfghjk»
Выход: Ошибка: Входные данные не являются списком продуктов. Повторите запрос.

Пример 7 (второе фото, слияние):
Предыдущий список: [{"name":"молоко","quantity":1,"unit":"л"}]
Вход: «ещё фото: молоко 0.5 л, хлеб»
Выход: {"products": [
  {"name":"молоко","quantity":1.5,"unit":"л","source":"merged","added_at":1},
  {"name":"хлеб","quantity":null,"unit":null,"source":"photo","added_at":2}],
 "confidence":0.95,"mode":"accumulate","duplicates_merged":1}

Пример 8 (конфликт единиц):
Предыдущий список: [{"name":"яйца","quantity":10,"unit":"шт"}]
Вход: «добавь яйца 1 кг»
Выход: {"products": [
  {"name":"яйца","quantity":10,"unit":"шт","source":"merged","added_at":1},
  {"name":"яйца","quantity":1,"unit":"кг","source":"text","added_at":2}],
 "confidence":0.6,"mode":"accumulate","duplicates_merged":0}

Пример 9 (ошибка шага без потери списка):
Предыдущий список: [{"name":"сыр","quantity":null,"unit":null}]
Вход: «авыавыа sdfghjk»
Выход: Ошибка шага: вход не является списком продуктов. Список не изменён.

# Поле confidence:
- 1.0 — все продукты распознаны однозначно;
- 0.7–0.9 — есть небольшие сомнения (например, продукт виден частично);
- 0.3–0.6 — распознавание неуверенное, часть данных размыта;
- 0.0–0.2 — почти ничего не удалось распознать.

Входные данные:
{{ input }}





