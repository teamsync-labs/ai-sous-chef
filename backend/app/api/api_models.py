from typing import Optional, List

from pydantic import BaseModel

class RecognizeInput(BaseModel):
    text: Optional[str] = None


class RecipesInput(BaseModel):
    products: List[str]


class RecipesOutput(BaseModel):
    recipes: List[dict[str, str | list[str]]]