from pydantic import SecretStr, EmailStr, BaseModel, Field
from modules.repository.response_models.auth import TokenResponse
from modules.repository.request_models.base import BaseReq, BaseResponse
from typing import Any


class LoginRequest(BaseReq):
    username: str | EmailStr
    password: SecretStr
    result: TokenResponse = TokenResponse()


class Grant(BaseModel):
    grant_type: str = Field(alias="grantType")
    token_id: str = Field(alias="tokenId")


class RefreshTokenRequest(BaseReq):
    result: TokenResponse = TokenResponse()


class EnableLocationRequest(BaseReq):
    token: str
    result: BaseResponse = BaseResponse()


class MFALoginRequest(BaseReq):
    claims: dict[str, Any]
    auth_method: str
    result: TokenResponse = TokenResponse()
