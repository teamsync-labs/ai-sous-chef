import base64
from typing import Optional, List, Any

from pydantic import BaseModel, model_validator, ConfigDict, Field, field_validator


class BaseAPIModel(BaseModel):
    pass


def coerce_img_base64(value: Any) -> Any:
    """JSON/ASCII base64 → сырые байты изображения; готовый JPEG/PNG/WebP не трогаем."""
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("data:") and "," in s:
            s = s.split(",", 1)[1]
        return base64.b64decode(s)
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        if (
            raw.startswith(b"\xff\xd8\xff")
            or raw.startswith(b"\x89PNG")
            or raw.startswith(b"RIFF")
        ):
            return raw
        # FastAPI/Pydantic иногда отдают base64-строку уже как utf-8 bytes («/9j/...»).
        if raw[:4] in (b"/9j/", b"iVBO", b"UklG"):
            return base64.b64decode(raw)
        return raw
    return value


class RecognizeInput(BaseAPIModel):
    text: Optional[str] = None
    # Клиенты шлют JSON-строку base64; без coerce оставался ASCII «/9j/...» → double-encode в engine.
    img_base64: Optional[bytes] = None

    @field_validator("img_base64", mode="before")
    @classmethod
    def _coerce_img_base64(cls, value: Any) -> Any:
        return coerce_img_base64(value)

    @model_validator(mode='after')
    def check_only_one_not_null(self) -> 'RecognizeInput':
        not_none_count = sum(
            field is not None for field in (self.text, self.img_base64)
        )

        if not_none_count != 1:
            raise ValueError('Только одно из полей text или img_base64 может быть заполнено (не null)')

        return self


class RecognizeResult(BaseAPIModel):
    model_config = ConfigDict(extra="ignore")
    products: List[str]
    confidence: float = Field(default=0.0, ge=0, le=1.0)


class RecipesInput(BaseAPIModel):
    products: List[str]


class RecipesResult(BaseAPIModel):
    recipes: List[dict[str, str | list[str]]] = Field(default_factory=list)
