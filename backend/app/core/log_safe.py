"""Безопасное логирование: обрезка длинных строк и маскирование идентификаторов.

Задача: не пускать в stdout сырые ответы LLM, base64, длинные
пользовательские тексты и чувствительные идентификаторы (Telegram id).
"""

from __future__ import annotations

_DEFAULT_LIMIT = 200


def truncate_for_log(text: str | None, limit: int = _DEFAULT_LIMIT) -> str:
    """Обрезает текст для лога и помечает исходную длину.

    - Короткий текст возвращается без изменений.
    - Длинный обрезается до ``limit`` символов, добавляется пометка длины.
    - ``None`` и пустая строка не роняют, возвращают маркеры.
    """
    if text is None:
        return "<none>"
    if not isinstance(text, str):
        text = str(text)
    if not text:
        return "<empty>"
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...<truncated, total_len={len(text)}>"


def mask_id(value: str | int | None) -> str:
    """Маскирует идентификатор, оставляя только последние 4 символа.

    Пример: ``123456789`` -> ``****6789``.
    """
    if value is None:
        return "<none>"
    s = str(value)
    if not s:
        return "<empty>"
    if len(s) <= 4:
        return f"****{s}"
    return f"****{s[-4:]}"