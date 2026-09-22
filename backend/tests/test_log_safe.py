"""Unit-тесты для хелпера безопасного логирования (log_safe.py)."""

from app.core.log_safe import mask_id, truncate_for_log


class TestTruncateForLog:
    """Тесты для truncate_for_log."""

    def test_short_text_unchanged(self):
        """Короткий текст возвращается без изменений."""
        assert truncate_for_log("short text") == "short text"

    def test_long_text_is_truncated(self):
        """Длинный текст обрезается, добавляется пометка длины."""
        long_text = "a" * 300
        result = truncate_for_log(long_text, limit=200)
        assert result.startswith("a" * 200)
        assert "total_len=300" in result
        assert len(result) > 200

    def test_none_does_not_raise(self):
        """None не роняет, возвращает маркер."""
        assert truncate_for_log(None) == "<none>"

    def test_empty_string_does_not_raise(self):
        """Пустая строка не роняет, возвращает маркер."""
        assert truncate_for_log("") == "<empty>"


class TestMaskId:
    """Тесты для mask_id."""

    def test_long_id_masked(self):
        """Длинный id маскируется, видны последние 4 символа."""
        assert mask_id("123456789") == "****6789"

    def test_short_id_masked(self):
        """Короткий id тоже маскируется."""
        assert mask_id("123") == "****123"

    def test_none_does_not_raise(self):
        """None не роняет, возвращает маркер."""
        assert mask_id(None) == "<none>"

    def test_int_id_supported(self):
        """Поддерживается int (Telegram id — int)."""
        assert mask_id(987654321) == "****4321"