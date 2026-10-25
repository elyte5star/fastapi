from modules.repository.request_models.base import BaseResponse
from pydantic import BaseModel, Field, Json, ConfigDict
from datetime import datetime
from typing import Optional, Annotated


class Address(BaseModel):
    first_name: Annotated[
        str,
        Field(serialization_alias="firstName"),
    ]
    last_name: Annotated[str, Field(serialization_alias="lastName")]
    street_address: Annotated[
        str,
        Field(
            serialization_alias="streetAddress",
        ),
    ]
    country: str
    state: str
    email: str
    zip_code: Annotated[
        str,
        Field(
            serialization_alias="zipCode",
        ),
    ]
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class AddressDisplay(Address):
    id: str
    user_id: str = Field(serialization_alias="userId")
    full_name: str = Field(serialization_alias="fullName")

    model_config = ConfigDict(from_attributes=True)


class BookingDisplay(BaseModel):
    id: str = Field(serialization_alias="userId")
    user_id: str = Field(serialization_alias="userId")
    cart: list[dict]
    total_price: float
    created_at: datetime = Field(serialization_alias="createdAt")
    address: Address = Field(serialization_alias="shippingAddress")

    model_config = ConfigDict(from_attributes=True)


class UserDisplay(BaseModel):
    id: str = Field(serialization_alias="userId")
    created_at: datetime = Field(serialization_alias="createdAt")
    modified_at: Optional[datetime] = Field(serialization_alias="modifiedAt")
    modified_by: Optional[str] = Field(
        default=None,
        serialization_alias="modifiedBy",
    )
    created_by: str = Field(serialization_alias="createdBy", exclude=True)
    type: str = Field(exclude=True)
    email: str
    username: str
    password: str = Field(exclude=True)
    active: bool
    enabled: bool
    admin: bool
    telephone: str
    failed_attempts: int = Field(
        serialization_alias="failedAttempts",
        exclude=True,
    )
    discount: float
    lock_time: Optional[datetime] = Field(serialization_alias="lockTime")
    is_using_mfa: bool = Field(serialization_alias="IsUsingMFA")
    is_locked: bool = Field(serialization_alias="accountLocked")
    # otp:
    # password_reset :
    locations: list = Field(default=[], exclude=True)
    addresses: list[AddressDisplay] = []
    bookings: list[BookingDisplay] = []

    model_config = ConfigDict(from_attributes=True, extra="allow")


class CreateUserResponse(BaseResponse):
    new_user: UserDisplay | None = Field(default=None, alias="user")


class GetUserResponse(BaseResponse):
    user: Optional[UserDisplay] = None


class GetUsersResponse(BaseResponse):
    users: list[UserDisplay] = []


class ClientEnquiryResponse(BaseResponse):
    eid: str = ""
