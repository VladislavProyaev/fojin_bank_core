from aio_pika.patterns import RPC
from fastapi import APIRouter, Depends, Request

from api.schemas.errors import BaseError
from api.schemas.user import User
from services.rabbit_mq.rabbit import get_rpc

main_router = APIRouter()


@main_router.get('/rpc')
async def rpc_test(rpc: RPC = Depends(get_rpc)):
    response = await rpc.proxy.remote_method()
    print(response)


@main_router.post(
    path='/user',
    status_code=201,
    responses={
        201: {'model': User},
        400: {'model': BaseError}
    },
    tags=['create_user']
)
async def create_user(
    request: Request,
    rpc: RPC = Depends(get_rpc)
) -> bool | BaseError:
    try:
        return True
    except Exception as exception:
        return BaseError(error=str(exception))
