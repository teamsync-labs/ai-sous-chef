from typing import Optional, List, Literal, Any
from pydantic import BaseModel, Field, model_validator, Base64Bytes


class BaseAPIModel(BaseModel):
    pass


class RecognizeInput(BaseAPIModel):
    text: Optional[str] = None
    img_base64: Optional[Base64Bytes] = None

    @model_validator(mode='after')
    def check_only_one_not_null(self) -> 'RecognizeInput':
        not_none_count = sum(
            field is not None for field in (self.text, self.img_base64)
        )

        if not_none_count != 1:
            raise ValueError('Только одно из полей text или img_base64 может быть заполнено (не null)')

        return self


class RecognizeResult(BaseAPIModel):
    products: List[str]
    confidence: float


class RecipesInput(BaseAPIModel):
    products: List[str]


class RecipesResult(BaseAPIModel):
    recipes: List[dict[str, str | list[str]]]


ConsentChannel = Literal["site", "bot", "app"]
ConsentType = Literal["privacy", "pdn", "analytics", "marketing"]
ConsentAction = Literal["granted", "withdrawn"]

_MAPPED_CHANNELS = {"bot", "app"}


def validate_consent_identity(
    channel: str | None,
    subject_id: str | None,
    external_id: str | None,
) -> None:
    if channel in _MAPPED_CHANNELS:
        if not external_id:
            raise ValueError("Для bot и app нужно поле external_id")
        if subject_id:
            raise ValueError("Для bot и app поле subject_id не используется")
        return
    if not subject_id:
        raise ValueError("Нужно поле subject_id")
    if external_id:
        raise ValueError("Поле external_id только для bot и app")


class ConsentRecordInput(BaseAPIModel):
    channel: ConsentChannel
    consent_type: ConsentType
    action: ConsentAction
    subject_id: Optional[str] = Field(None, min_length=1, max_length=256)
    external_id: Optional[str] = Field(None, min_length=1, max_length=256)

    @model_validator(mode="after")
    def check_identity(self) -> "ConsentRecordInput":
        validate_consent_identity(self.channel, self.subject_id, self.external_id)
        return self


class ConsentWithdrawInput(BaseAPIModel):
    consent_type: Optional[ConsentType] = None
    channel: Optional[ConsentChannel] = None
    subject_id: Optional[str] = Field(None, min_length=1, max_length=256)
    external_id: Optional[str] = Field(None, min_length=1, max_length=256)
    erase: bool = False

    @model_validator(mode="after")
    def check_identity(self) -> "ConsentWithdrawInput":
        validate_consent_identity(self.channel, self.subject_id, self.external_id)
        return self


class ConsentProxyResult(BaseAPIModel):
    ok: bool = True
    journal: Optional[dict[str, Any]] = None
