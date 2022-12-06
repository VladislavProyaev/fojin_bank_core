from fastapi import APIRouter, FastAPI

from api.methods.users import authorization_router

app = FastAPI()


def init_routers():
    base_router = APIRouter()
    app.include_router(base_router)
    app.include_router(authorization_router)
