import json
from fastapi import Response
from modules.repository.request_models.auth import BaseResponse, MFALoginRequest
from modules.service.auth import AuthenticationHandler
from modules.utils.misc import get_indent


class MFAHandler(AuthenticationHandler):

    async def authenticate_ext_user(
        self, req: MFALoginRequest, response: Response
    ) -> BaseResponse:
        if not (req.claims and req.auth_method):
            return req.req_failure("Couldnt not verify audience.")
        email = self.get_email_from_claims(req.claims, req.auth_method)
        user_in_db = await self.find_user_by_email(email)
        if user_in_db is not None:
            if not user_in_db.enabled or user_in_db.is_locked:
                return req.req_failure(
                    " Account unverified or locked. Please, contact admin "
                )
            if not user_in_db.is_using_mfa:
                return req.req_failure("MFA is disabled for this account ")
            data = {
                "userId": user_in_db.id,
                "sub": user_in_db.username,
                "email": user_in_db.email,
                "admin": user_in_db.admin,
                "enabled": user_in_db.enabled,
                "active": user_in_db.active,
                "role": ["USER"] if not user_in_db.admin else ["USER", "ADMIN"],
                "jti": get_indent(),
                "discount": user_in_db.discount,
            }
            token_data = await self.create_token_response(user_in_db, data)
            self.create_cookie(token_data.pop("refreshToken"), response)
            req.result.data = token_data
            return req.req_success(
                f"User with username/email: {user_in_db.username} is authorized"
            )
        return req.req_failure(f"User with email {email} is not authorized.")

    def get_email_from_claims(self, verified_claims: dict, auth_method: str) -> str:
        if auth_method == "MSAL":
            return verified_claims["preferred_username"]
        return verified_claims["email"]
