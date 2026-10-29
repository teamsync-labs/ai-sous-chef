from typing import Optional, Literal, Any

from pydantic import Field, model_validator

from ..api_models import BaseAPIModel

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
