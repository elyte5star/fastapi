from pydantic import (
    EmailStr,
    model_validator,
    FilePath,
    BaseModel,
    Field,
    computed_field,
)
from fastapi.exceptions import RequestValidationError
from typing_extensions import Self
from modules.repository.request_models.base import BaseResponse
from modules.repository.response_models.user import (
    CreateUserResponse,
    GetUserResponse,
    GetUsersResponse,
    ClientEnquiryResponse,
)
from modules.repository.validators.base import (
    ValidateTelephone,
    ValidateUsername,
    ValidatePassword,
    ValidateUUID,
    VerifyEmail,
)
from modules.repository.request_models.base import BaseReq
from typing import Any, Optional
from modules.utils.misc import get_indent


class CreateUser(BaseModel):
    username: ValidateUsername
    email: VerifyEmail
    password: ValidatePassword
    confirm_password: ValidatePassword = Field(
        validation_alias="confirmPassword",
    )
    telephone: ValidateTelephone
    active: bool = True

    @model_validator(mode="after")
    def verify_password(self) -> Self:
        if self.password != self.confirm_password:
            raise RequestValidationError("password and confirm password do not match")
        return self

    @computed_field
    @property
    def created_by(self) -> str:
        return self.username

    @computed_field
    def id(self) -> str:
        return get_indent()

    @computed_field
    def discount(self) -> float:
        return 0.0


class CreateUserRequest(BaseReq):
    new_user: CreateUser
    result: CreateUserResponse = CreateUserResponse()


class LockUserAccountRequest(BaseReq):
    userid: ValidateUUID
    result: BaseResponse = BaseResponse()


class UnLockUserRequest(LockUserAccountRequest):
    pass


class GetUserRequest(BaseReq):
    userid: ValidateUUID
    result: GetUserResponse = GetUserResponse()


class DeleteUserRequest(BaseReq):
    userid: ValidateUUID
    result: BaseResponse = BaseResponse()


class GetUsersRequest(BaseReq):
    result: GetUsersResponse = GetUsersResponse()


class EmailRequestSchema(BaseModel):
    subject: str
    recipients: list[EmailStr]
    body: dict[str, Any]
    file: Optional[FilePath] = None
    template_name: str | None = None


class OtpRequest(BaseReq):
    email: EmailStr
    result: BaseResponse = BaseResponse()


class NewOtpRequest(BaseReq):
    token: str
    result: BaseResponse = BaseResponse()


class VerifyRegistrationOtpRequest(BaseReq):
    token: str
    result: BaseResponse = BaseResponse()


class UserEnquiry(BaseModel):
    client_name: str = Field(
        min_length=3,
        max_length=10,
        validation_alias="clientName",
    )
    client_email: VerifyEmail = Field(validation_alias="clientEmail")
    country: str
    subject: str
    message: str = Field(min_length=3, max_length=500)

    @computed_field
    @property
    def created_by(self) -> str:
        return self.client_name

    @computed_field
    def id(self) -> str:
        return get_indent()

    @computed_field
    def is_closed(self) -> bool:
        return False


class UserEnquiryRequest(BaseReq):
    enquiry: UserEnquiry
    result: ClientEnquiryResponse = ClientEnquiryResponse()


class ResetUserPassword(BaseModel):
    email: VerifyEmail


class ResetUserPasswordRequest(BaseReq):
    data: ResetUserPassword
    result: BaseResponse = BaseResponse()


class UpdateUserPassword(BaseModel):
    old_password: str = Field(alias="oldPassword")
    new_password: ValidatePassword = Field(alias="newPassword")
    confirm_password: ValidatePassword = Field(alias="confirmPassword")

    @model_validator(mode="after")
    def verify_password(self) -> Self:
        if self.new_password == self.old_password:
            raise RequestValidationError(
                "old password cannot be the same as new password."
            )
        if self.new_password != self.confirm_password:
            raise RequestValidationError(
                "new password and confirm password do not match"
            )
        return self


class ChangePassword(BaseModel):
    new_password: ValidatePassword = Field(alias="newPassword")
    confirm_password: ValidatePassword = Field(alias="confirmPassword")
    token: str

    @model_validator(mode="after")
    def verify_password(self) -> Self:
        if self.new_password != self.confirm_password:
            raise RequestValidationError(
                "new password and confirm password do not match"
            )
        return self


class UpdateUserPasswordRequest(BaseReq):
    data: UpdateUserPassword
    userid: ValidateUUID
    result: BaseResponse = BaseResponse()


class SaveUserPassswordRequest(BaseReq):
    data: ChangePassword
    result: BaseResponse = BaseResponse()


class EnableMFALoginRequest(BaseReq):
    userid: ValidateUUID
    result: BaseResponse = BaseResponse()
