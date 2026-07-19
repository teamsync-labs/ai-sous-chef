from typing import Optional, List
from pydantic import BaseModel, model_validator, Base64Str


class BaseAPIModel(BaseModel):
    pass

class RecognizeInput(BaseAPIModel):
    text: Optional[str] = None
    img_base64: Optional[Base64Str] = None

    @model_validator(mode='after')
    def check_only_one_not_null(self) -> 'RecognizeInput':
        values = self.model_dump()
        not_none_count = sum(
            1 for field in ('text', 'img_base64')
            if values.get(field) is not None
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