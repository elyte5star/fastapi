from modules.repository.request_models.base import BaseResponse
from pydantic import Field, BaseModel


class TokenData(BaseModel):
    userid: str = Field(default="", alias="userId")
    username: str = ""
    email: str = ""
    enabled: bool = False
    admin: bool = False
    access_token: str = Field(default="", alias="accessToken")
    refresh_token: str = Field(default="", alias="refreshToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    is_locked: bool = Field(default=True, alias="accountNonLocked")
    token_id: str = Field(default="", alias="tokenId")


class TokenResponse(BaseResponse):
    data: dict = Field(default={})
