from modules.repository.request_models.auth import (
    LoginRequest,
    EnableLocationRequest,
    RefreshTokenRequest,
    BaseResponse,
)
import bcrypt
from modules.repository.validators.base import is_valid_email
from typing import Optional
from datetime import timedelta
from jose import jwt
from modules.utils.misc import time_delta, date_time_now_utc_tz, get_indent
from modules.database.schema.user import User
from fastapi import Request, Response
from modules.security.login_attempt import LoginAttemptChecker


class AuthenticationHandler(LoginAttemptChecker):
    async def authenticate_user(
        self, req: LoginRequest, request: Request, response: Response
    ) -> BaseResponse:
        is_email, email = is_valid_email(req.username)
        user = None
        if is_email:
            user = await self.find_user_by_email(email)
        else:
            user = await self.get_user_by_username(req.username)
        if user is not None:
            if not user.enabled or user.is_locked:
                return req.req_failure(
                    " Account unverified or locked. Please, contact admin "
                )
            if self.verify_password(
                req.password.get_secret_value(),
                user.password,
            ):
                strange_loc = await self.on_login_success(user, request)
                if strange_loc:
                    return req.req_failure(
                        "Login attempt from different location",
                    )
                data = {
                    "userId": user.id,
                    "sub": user.username,
                    "email": user.email,
                    "admin": user.admin,
                    "enabled": user.enabled,
                    "active": user.active,
                    "roles": ["USER"] if not user.admin else ["USER", "ADMIN"],
                    "jti": get_indent(),
                    "discount": user.discount,
                }
                token_data = await self.create_token_response(user, data)
                self.create_cookie(token_data.pop("refreshToken"), response)
                req.result.data = token_data
                return req.req_success(
                    f"User with username/email : {req.username} is authorized"
                )
        await self.on_login_failure(user, request)
        return req.req_failure(
            f"User {req.username} is not authorized.Incorrect username or password"
        )

    async def on_login_success(self, user: User, request: Request) -> bool:
        if user.failed_attempts > 0 or self.cf.failed_login_attempt_count > 0:
            await self.reset_failed_attempts(user)
        is_strange = await self.check_strange_location(user, request)
        if is_strange:
            return True
        await self.login_notification(user, request)
        return False

    async def on_login_failure(self, user: User | None, request: Request):
        if user is None:
            await self.increase_unknown_user_failed_attempts(request)
        else:
            await self.increase_user_failed_attempts(user)

    async def create_token_response(self, user: User, data: dict) -> dict:
        access_token_expiry = time_delta(self.cf.token_expire_min)
        refresh_token_expiry = time_delta(self.cf.refresh_token_expire_min)
        refresh_token = self.create_token(
            data=data,
            expires_delta=refresh_token_expiry,
        )
        access_token = self.create_token(
            data=data,
            expires_delta=access_token_expiry,
        )
        return dict(
            userId=user.id,
            username=user.username,
            email=user.email,
            enabled=user.enabled,
            admin=user.admin,
            accessToken=access_token,
            refreshToken=refresh_token,
            accountNonLocked=not user.is_locked,
            tokenId=data["jti"],
            tokenType="Bearer",
        )

    def verify_password(
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        return bcrypt.checkpw(
            plain_password.encode(self.cf.encoding),
            hashed_password.encode(self.cf.encoding),
        )

    def create_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ):
        to_encode = data.copy()
        if expires_delta:
            _expire = date_time_now_utc_tz() + expires_delta
        else:
            _expire = date_time_now_utc_tz() + time_delta(
                self.cf.token_expire_min,
            )
        to_encode.update({"exp": _expire})
        jwt_encode = jwt.encode(
            to_encode, self.cf.secret_key, algorithm=self.cf.algorithm
        )
        return jwt_encode

    # LOGIN LOCATION
    async def _enable_new_loc(
        self,
        req: EnableLocationRequest,
    ) -> BaseResponse:
        country = await self.is_valid_new_location_token(req.token)
        if country is not None:
            return req.req_success(f"{country} enabled.")
        return req.req_failure("Invalid Login Location!")

    async def is_valid_new_location_token(self, token: str) -> str | None:
        new_loc_token = await self.find_new_location_by_token_query(token)
        if new_loc_token is not None:
            user_loc = new_loc_token.location
            await self.update_user_loc_query(
                user_loc.id,
                dict(enabled=True),
            )
            await self.del_new_location_query(new_loc_token.id)
            return user_loc.country
        return None

    async def _refresh_access_token(
        self,
        req: RefreshTokenRequest,
    ) -> BaseResponse:
        current_user = req.credentials
        if current_user is not None:
            data = {
                "userId": current_user.user_id,
                "sub": current_user.username,
                "email": current_user.email,
                "admin": current_user.admin,
                "enabled": current_user.enabled,
                "active": current_user.active,
                "roles": current_user.roles,
                "jti": get_indent(),
                "discount": current_user.discount,
            }
            access_token_expiry = time_delta(self.cf.token_expire_min)
            access_token = self.create_token(
                data=data,
                expires_delta=access_token_expiry,
            )
            req.result.data = dict(
                accessToken=access_token,
                userId=current_user.user_id,
                username=current_user.username,
                email=current_user.email,
            )
            return req.req_success(
                f"User with username/email : {data["sub"]} is authorized"
            )
        return req.req_failure("Could not validate credentials")

    def create_cookie(self, token: str, response: Response) -> None:
        max_age = self.cf.refresh_token_expire_min * 24 * 60 * 60
        response.set_cookie(
            key="refresh-token",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=max_age,
        )
