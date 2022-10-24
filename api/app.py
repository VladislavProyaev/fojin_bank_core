from fastapi import APIRouter, FastAPI

from api.routes.main import main_router

app = FastAPI()


def init_routers():
    base_router = APIRouter()
    base_router.include_router(main_router)

    app.include_router(base_router)
