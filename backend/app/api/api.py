from fastapi import APIRouter
from .api_models import RecipesInput, RecipesOutput

router = APIRouter(
    prefix="/app/api",
    tags=["MVP API"]
)


@router.post("/recognize")
async def recognize():
    return {"status": "ok"}

@router.post("/recipes", response_model=RecipesOutput)
async def recipes(recipes_input: RecipesInput):
    return RecipesOutput(recipes=mock_generate_recipes(recipes_input))


# region mock funcs
def mock_generate_recipes(products: RecipesInput):
    return [{
        "title": "Спагетти карбонара",
        "steps": [
            "Отварить спагетти до состояния al dente.",
            "Обжарить бекон до золотистой корочки.",
            "Смешать яйца с тёртым сыром и перцем.",
            "Добавить спагетти к бекону.",
            "Снять сковороду с огня и вмешать яичную смесь.",
        ],
    },
    {
        "title": "Куриный суп",
        "steps": [
            "Залить курицу водой и довести до кипения.",
            "Добавить нарезанный картофель.",
            "Обжарить лук и морковь.",
            "Добавить овощи и лапшу в суп.",
            "Варить до готовности и посолить.",
        ],
    },
    {
        "title": "Омлет с сыром",
        "steps": [
            "Разбить яйца в миску.",
            "Добавить молоко и соль.",
            "Взбить смесь венчиком.",
            "Вылить смесь на разогретую сковороду.",
            "Посыпать сыром и готовить под крышкой.",
        ],
    }]


# endregion