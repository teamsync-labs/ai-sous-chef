from .other import router as other_router
from .recognize import router as recognize_router
from .start import router as start_router
from .delete import router as delete_router
from .help import router as help_router


routers = [
    start_router,
    delete_router,
    help_router,
    recognize_router,
    other_router
]
