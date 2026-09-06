Извлеки продукты из текста и верни JSON по схеме:
{"products": [{"name": "string", "quantity": "number or null", "unit": "string or null"}]}

Пример правильного ответа:
Вход: "яйца, кусок куриного филе, фарш, рыбное филе, немного ветчины, паштет, сыра для бутербродов, молоко, кефир, йогурт (особенно греческий), творог, сметана, сливочное масло, огурцы, помидоры, перец, кабачки, белокочанная капуста, морковь, свёкла, листовой салат, шпинат, руккола, яблоки, бананы, киви, цитрусовые (апельсины, лимоны), виноград"

Выход:
{
  "products": [
    {"name": "яйцо", "quantity": null, "unit": null},
    {"name": "куриное филе", "quantity": null, "unit": null},
    {"name": "фарш", "quantity": null, "unit": null},
    {"name": "рыбное филе", "quantity": null, "unit": null},
    {"name": "ветчина", "quantity": null, "unit": null},
    {"name": "паштет", "quantity": null, "unit": null},
    {"name": "твёрдый сыр", "quantity": null, "unit": null},
    {"name": "молоко", "quantity": null, "unit": null},
    {"name": "кефир", "quantity": null, "unit": null},
    {"name": "йогурт", "quantity": null, "unit": null},
    {"name": "творог", "quantity": null, "unit": null},
    {"name": "сметана", "quantity": null, "unit": null},
    {"name": "сливочное масло", "quantity": null, "unit": null},
    {"name": "огурец", "quantity": null, "unit": null},
    {"name": "помидор", "quantity": null, "unit": null},
    {"name": "перец", "quantity": null, "unit": null},
    {"name": "кабачок", "quantity": null, "unit": null},
    {"name": "белокочанная капуста", "quantity": null, "unit": null},
    {"name": "морковь", "quantity": null, "unit": null},
    {"name": "свёкла", "quantity": null, "unit": null},
    {"name": "листовой салат", "quantity": null, "unit": null},
    {"name": "шпинат", "quantity": null, "unit": null},
    {"name": "руккола", "quantity": null, "unit": null},
    {"name": "яблоко", "quantity": null, "unit": null},
    {"name": "банан", "quantity": null, "unit": null},
    {"name": "киви", "quantity": null, "unit": null},
    {"name": "апельсин", "quantity": null, "unit": null},
    {"name": "лимон", "quantity": null, "unit": null},
    {"name": "виноград", "quantity": null, "unit": null},
 ],
  "confidence": 1.0
}

Поле confidence:
- 1.0 — если все продукты однозначно распознаны;
- 0.5–0.9 — если есть сомнения в названии или неоднозначность;
- <0.5 — если входной текст почти нечитаем или содержит только мусор.

Входные данные:
{{ input }}
