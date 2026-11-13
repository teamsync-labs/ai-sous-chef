"""
Клиент (приложение/бот) шлёт img_base64 как base64-строку в JSON.
RecognizeInput должен декодировать её в сырые байты изображения (JPEG magic FF D8 FF),
а не оставлять ASCII «/9j/...» — иначе ai_engine делает повторный b64encode.
"""

import base64
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.api_models import RecognizeInput, RecognizeResult
from app.main import app

# Минимальный JPEG (1x1) — начинается с FF D8 FF
_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDAREAAhEBAxEB/8QAF"
    "AABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDA"
    "QACEQMRAD8AfwD/2Q=="
)
_JPEG_B64 = base64.b64encode(_JPEG).decode("ascii")

client = TestClient(app)
_API_HEADERS = {"X-Api-Key": "test-bot-key"}


class TestRecognizeInputImgBase64:
    def test_decodes_base64_string_to_jpeg_bytes(self):
        inp = RecognizeInput.model_validate({"img_base64": _JPEG_B64})
        assert inp.img_base64 is not None
        assert inp.img_base64[:3] == b"\xff\xd8\xff"
        assert inp.img_base64 == _JPEG

    def test_accepts_already_decoded_jpeg_bytes(self):
        inp = RecognizeInput(img_base64=_JPEG)
        assert inp.img_base64 == _JPEG

    def test_decodes_data_url_prefix(self):
        inp = RecognizeInput.model_validate(
            {"img_base64": f"data:image/jpeg;base64,{_JPEG_B64}"}
        )
        assert inp.img_base64 == _JPEG


def test_recognize_api_passes_decoded_jpeg_to_engine():
    """JSON base64-строка с камеры не должна доходить до engine как ASCII /9j/."""
    captured: dict = {}

    async def _fake_recognize(recognize_input: RecognizeInput):
        captured["img"] = recognize_input.img_base64
        return RecognizeResult(products=["молоко"], confidence=0.9)

    engine = AsyncMock()
    engine.recognize_products = _fake_recognize

    with patch("app.api.api.get_ai_engine", return_value=engine):
        response = client.post(
            "/app/api/recognize",
            headers=_API_HEADERS,
            json={"img_base64": _JPEG_B64},
        )

    assert response.status_code == 200
    assert captured["img"][:3] == b"\xff\xd8\xff"
    assert captured["img"] == _JPEG
