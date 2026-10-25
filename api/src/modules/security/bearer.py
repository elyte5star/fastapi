from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from starlette.requests import Request
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import HTTPBearer as HTTPBearerModel
from jose import JWTError, jwt
import time
from modules.settings.configuration import ApiConfig
from modules.repository.queries.common import CommonQueries
from modules.security.current_user import JWTPrincipal
from fastapi.security.base import SecurityBase
from fastapi.exceptions import HTTPException


cfg = ApiConfig().from_toml_file().from_env_file()


queries = CommonQueries(cfg)


class JWTBearer(SecurityBase):

    def __init__(
        self,
        scheme_name: str | None = None,
        auto_error: bool = True,
        allowed_roles: list = cfg.roles,
        auth_method: str | None = None,
    ) -> None:
        super().__init__()
        self.auto_error = auto_error
        self.scheme_name = scheme_name or self.__class__.__name__
        self.allowed_roles = allowed_roles
        self.model = HTTPBearerModel(
            description="Bearer token",
        )

    async def __call__(self, request: Request) -> JWTPrincipal | None:
        authorization = request.headers.get("Authorization", None)
        scheme, token = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and token):
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            else:
                return None
        if self.verify_jwt(token) is None:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Invalid token or expired token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        current_user = await self.check_user(self.payload["userId"])
        return current_user

    async def check_user(self, user_id: str) -> JWTPrincipal:
        db_user = await queries.find_user_by_id(user_id)
        if db_user is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="User session not found",
            )
        roles = ["USER"] if not db_user.admin else ["USER", "ADMIN"]
        matches = set(self.allowed_roles).intersection(set(roles))
        if len(matches) == 0:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        current_user = JWTPrincipal(
            user_id=self.payload["userId"],
            email=self.payload["email"],
            username=self.payload["sub"],
            active=self.payload["active"],
            enabled=self.payload["enabled"],
            expires=self.payload["exp"],
            admin=self.payload["admin"],
            roles=self.payload["roles"],
            discount=self.payload["discount"],
            token_id=self.payload["jti"],
        )
        return current_user

    def verify_jwt(self, token: str) -> dict | None:
        if token is None:
            return None
        try:
            self.payload = jwt.decode(
                token,
                cfg.secret_key,
                algorithms=[cfg.algorithm],
            )
            return self.payload if self.payload["exp"] >= time.time() else None
        except JWTError:
            return None
