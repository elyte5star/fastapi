from modules.service.user import UserHandler
from fastapi import APIRouter, Depends, status, Request
from typing import Annotated
from modules.repository.response_models.user import (
    GetUserResponse,
    CreateUserResponse,
    GetUsersResponse,
    BaseResponse,
    ClientEnquiryResponse,
)
from modules.repository.request_models.user import (
    CreateUserRequest,
    GetUserRequest,
    GetUsersRequest,
    DeleteUserRequest,
    OtpRequest,
    NewOtpRequest,
    VerifyRegistrationOtpRequest,
    CreateUser,
    UserEnquiryRequest,
    UserEnquiry,
    ResetUserPasswordRequest,
    ResetUserPassword,
    UpdateUserPassword,
    UpdateUserPasswordRequest,
    SaveUserPassswordRequest,
    ChangePassword,
    LockUserAccountRequest,
    UnLockUserRequest,
    EnableMFALoginRequest,
)
from modules.security.dependency import security, JWTBearer
from modules.security.current_user import JWTPrincipal
from pydantic import EmailStr
from modules.repository.validators.base import ValidateUUID


class UserRouter(UserHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(prefix="/user", tags=["User"])
        self.router.add_api_route(
            path="/signup",
            status_code=status.HTTP_201_CREATED,
            endpoint=self.create_user,
            response_model=CreateUserResponse,
            methods=["POST"],
            description="Create user account",
        )
        self.router.add_api_route(
            path="/create-registration-otp/{email}",
            status_code=status.HTTP_202_ACCEPTED,
            endpoint=self.create_verification_otp,
            response_model=BaseResponse,
            methods=["GET"],
            description="Admin send user verification code",
        )

        self.router.add_api_route(
            path="/signup/resend-registration-otp/{token}",
            status_code=status.HTTP_202_ACCEPTED,
            endpoint=self.resend_verification_otp,
            response_model=BaseResponse,
            methods=["GET"],
            description="Send a new user verification code",
        )
        self.router.add_api_route(
            path="/{userId}",
            endpoint=self.get_user,
            response_model=GetUserResponse,
            methods=["GET"],
            description="Get User",
        )

        self.router.add_api_route(
            path="/{userId}",
            endpoint=self.delete_user,
            response_model=BaseResponse,
            methods=["DELETE"],
            description="Delete User",
        )
        self.router.add_api_route(
            path="/enable-mfa/{userId}",
            endpoint=self.enable_ext_login,
            response_model=BaseResponse,
            methods=["GET"],
            description="Enable External Login",
        )
        self.router.add_api_route(
            path="/lock-account/{userId}",
            endpoint=self.lock_user_account,
            response_model=BaseResponse,
            methods=["GET"],
            description="Lock User Account",
        )
        self.router.add_api_route(
            path="/unlock-account/{userId}",
            endpoint=self.unlock_user_account,
            response_model=BaseResponse,
            methods=["GET"],
            description="Unlock User Account",
        )
        self.router.add_api_route(
            path="",
            endpoint=self.get_users,
            response_model=GetUsersResponse,
            methods=["GET"],
            description="Get Users, Admin right required",
        )

        self.router.add_api_route(
            path="/signup/verify-otp/{token}",
            endpoint=self.verify_registration_otp,
            response_model=BaseResponse,
            methods=["GET"],
            description="Confirm user registration",
        )
        self.router.add_api_route(
            path="/customer/service",
            endpoint=self.create_enquiry,
            response_model=ClientEnquiryResponse,
            summary="Customer Service",
            methods=["POST"],
        )

        self.router.add_api_route(
            path="/reset-password",
            endpoint=self.reset_user_password,
            response_model=BaseResponse,
            summary="Reset user password",
            methods=["POST"],
        )

        self.router.add_api_route(
            path="/update-password/{userId}",
            endpoint=self.update_user_password,
            response_model=BaseResponse,
            summary="Update user password",
            methods=["PUT"],
        )

        self.router.add_api_route(
            path="/save-password",
            endpoint=self.save_user_password,
            response_model=BaseResponse,
            summary="Save user password",
            methods=["POST"],
        )

    async def create_user(
        self, new_user: Annotated[CreateUser, Depends()], request: Request
    ) -> BaseResponse:
        return await self._create_user(
            CreateUserRequest(new_user=new_user),
            request,
        )

    async def get_users(
        self,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ) -> BaseResponse:
        return await self._get_users(GetUsersRequest(credentials=current_user))

    async def lock_user_account(
        self,
        userId: ValidateUUID,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ) -> BaseResponse:
        return await self._lock_user(
            LockUserAccountRequest(
                credentials=current_user,
                userid=userId,
            )
        )

    async def enable_ext_login(
        self,
        userId: ValidateUUID,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> BaseResponse:
        return await self._enable_ext_login(
            EnableMFALoginRequest(userid=userId, credentials=current_user)
        )
        pass

    async def unlock_user_account(
        self,
        userId: ValidateUUID,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ) -> BaseResponse:
        return await self._unblock_user(
            UnLockUserRequest(
                credentials=current_user,
                userid=userId,
            )
        )

    async def get_user(
        self,
        userId: ValidateUUID,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> BaseResponse:
        return await self._get_user(
            GetUserRequest(credentials=current_user, userid=userId)
        )

    async def delete_user(
        self,
        userId: ValidateUUID,
        current_user: Annotated[
            JWTPrincipal,
            Depends(security),
        ],
    ) -> BaseResponse:
        return await self._delete_user(
            DeleteUserRequest(credentials=current_user, userid=userId)
        )

    async def create_verification_otp(
        self,
        email: EmailStr,
        request: Request,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ) -> BaseResponse:
        return await self._create_verification_otp(
            OtpRequest(credentials=current_user, email=email), request
        )

    async def resend_verification_otp(
        self,
        token: str,
        request: Request,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ) -> BaseResponse:
        return await self._generate_new_otp(
            NewOtpRequest(token=token, credentials=current_user),
            request,
        )

    async def verify_registration_otp(self, token: str) -> BaseResponse:
        return await self.confirm_user_registration(
            VerifyRegistrationOtpRequest(token=token)
        )

    async def create_enquiry(
        self,
        enquiry: Annotated[UserEnquiry, Depends()],
        request: Request,
    ) -> BaseResponse:
        return await self._create_enquiry(
            UserEnquiryRequest(enquiry=enquiry),
            request,
        )

    async def reset_user_password(
        self, data: Annotated[ResetUserPassword, Depends()], request: Request
    ) -> BaseResponse:
        return await self._reset_user_password(
            ResetUserPasswordRequest(data=data),
            request,
        )

    async def update_user_password(
        self,
        userId: ValidateUUID,
        data: UpdateUserPassword,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> BaseResponse:
        return await self._update_user_password(
            UpdateUserPasswordRequest(
                credentials=current_user,
                userid=userId,
                data=data,
            )
        )

    async def save_user_password(
        self, data: Annotated[ChangePassword, Depends()]
    ) -> BaseResponse:
        return await self._save_user_password(
            SaveUserPassswordRequest(
                data=data,
            )
        )
