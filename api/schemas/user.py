from datetime import datetime

from pydantic import BaseModel, UUID4, Field, validator


class UserCreate(BaseModel):
    name: str
    surname: str
    phone: int
    city: str
    password: str


class TokenBase(BaseModel):
    token: UUID4 = Field(..., alias="access_token")
    expires: datetime
    token_type: str | None = "bearer"

    class Config:
        allow_population_by_field_name = True

    @classmethod
    @validator("token")
    def hexlify_token(cls, value: UUID4):
        return value.hex
