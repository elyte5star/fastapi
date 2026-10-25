from pydantic import BaseModel, Field


class JWTPrincipal(BaseModel):
    user_id: str = Field(serialization_alias="userId")
    username: str
    email: str
    active: bool
    enabled: bool
    roles: list[str]
    admin: bool
    expires: float
    discount: float
    token_id: str = Field(serialization_alias="tokenId")