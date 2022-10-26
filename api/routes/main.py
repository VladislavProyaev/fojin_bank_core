from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

main_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@main_router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return {
        "access_token": token.access_token, "token_type": token.token_type
    }
