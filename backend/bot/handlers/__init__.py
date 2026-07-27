from .other import router as other_router
from .recipes import router as recipes_router
from .recognize import router as recognize_router
from .start import router as start_router


routers = [
    start_router,
    recognize_router,
    recipes_router,
    other_router
]
