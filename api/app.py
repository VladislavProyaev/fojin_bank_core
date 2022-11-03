from fastapi import APIRouter, FastAPI

app = FastAPI()


def init_routers():
    base_router = APIRouter()

    app.include_router(base_router)
