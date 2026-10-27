from typing import Literal

from pydantic import BaseModel, model_validator, Field


class BaseAPIModel(BaseModel):
    pass


class RecognizeInput(BaseAPIModel):
    text: str | None = None
    img_base64: bytes | None = None

    @model_validator(mode='after')
    def check_only_one_not_null(self) -> 'RecognizeInput':
        not_none_count = sum(
            field is not None for field in (self.text, self.img_base64)
        )

        if not_none_count == 0:
            raise ValueError(
                'Не передано ни text, ни img_base64')
        if not_none_count > 1:
            raise ValueError(
                "Можно передать только одно из: text или img_base64"
            )

        return self


class ProductInput(BaseAPIModel):
    name: str
    quantity: float | None = None
    unit: Literal["шт", "кг", "г", "л", "мл"] | None = None


class Product(ProductInput):
    source: Literal["photo", "text", "merged"] | None = None
    added_at: float | None = None


class RecognizeResult(BaseAPIModel):
    products: list[Product]
    confidence: float = Field(default=0.0, ge=0, le=1.0)
    mode: Literal["single", "accumulate"] = "single"
    duplicates_merged: int = 0


class RecipesInput(BaseAPIModel):
    products: list[ProductInput]


class RecipeInput(BaseAPIModel):
    title: str
    steps: list[str]


class RecipesResult(BaseAPIModel):
    recipes: list[RecipeInput]
