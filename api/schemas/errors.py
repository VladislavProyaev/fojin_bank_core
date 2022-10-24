from pydantic import BaseModel


class BaseError(BaseModel):
    error: str | None
    detail: str | None
