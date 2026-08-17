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
ConsentSubjectChannel = Literal["bot", "app"]
ConsentType = Literal["privacy", "pdn", "analytics", "marketing"]
ConsentAction = Literal["granted", "withdrawn"]


class ConsentRecordInput(BaseAPIModel):
    subject_id: str = Field(min_length=1, max_length=256)
    channel: ConsentChannel
    consent_type: ConsentType
    action: ConsentAction


class ConsentWithdrawInput(BaseAPIModel):
    subject_id: str = Field(min_length=1, max_length=256)
    consent_type: Optional[ConsentType] = None
    channel: Optional[ConsentChannel] = None
    erase: bool = False


class ConsentProxyResult(BaseAPIModel):
    ok: bool = True
    journal: Optional[dict[str, Any]] = None


class ConsentSubjectInput(BaseAPIModel):
    channel: ConsentSubjectChannel
    external_id: str = Field(min_length=1, max_length=256)


class ConsentSubjectResult(BaseAPIModel):
    id: str
