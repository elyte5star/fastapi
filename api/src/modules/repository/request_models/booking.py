from pydantic import BaseModel, Field, ConfigDict, SecretStr
from modules.repository.validators.base import VerifyEmail, ValidateUUID
from modules.repository.request_models.base import BaseReq
from modules.repository.response_models.booking import (
    GetBookingResponse,
)
from typing_extensions import Annotated
import datetime
from modules.repository.response_models.job import GetJobRequestResponse
from modules.queue.models import CartItem, ShippingAddress


class BillingAddress(BaseModel):
    b_first_name: Annotated[str, Field(validation_alias="bfirstName")]
    b_last_name: Annotated[str, Field(validation_alias="blastName")]
    b_email: Annotated[
        VerifyEmail,
        Field(validation_alias="bemail"),
    ]
    b_address: Annotated[str, Field(validation_alias="baddress")]
    b_country: Annotated[str, Field(validation_alias="bcountry")]
    b_zip: Annotated[str, Field(validation_alias="bzip")]
    b_city: Annotated[str, Field(validation_alias="bcity")]


class PaymentDetails(BaseModel):
    card_type: Annotated[str, Field(validation_alias="cardType")]
    card_number: Annotated[SecretStr, Field(validation_alias="cardNumber")]
    expiry_date: Annotated[datetime.date, Field(validation_alias="expiryDate")]
    card_cvv: Annotated[SecretStr, Field(validation_alias="cardCvv")]
    name_on_card: Annotated[
        str,
        Field(validation_alias="nameOnCard"),
    ]
    currency: str = "NOK"
    billing_address: Annotated[
        BillingAddress,
        Field(validation_alias="billingAddress"),
    ]
    model_config = ConfigDict(extra="forbid")


class CreateBooking(BaseModel):
    cart: list[CartItem]
    payment_details: Annotated[
        PaymentDetails,
        Field(validation_alias="paymentDetails"),
    ]
    shipping_address: Annotated[
        ShippingAddress, Field(validation_alias="shippingAddress")
    ]
    user_id: ValidateUUID = Field(validation_alias="userId")
    model_config = ConfigDict(extra="forbid")


class CreateBookingRequest(BaseReq):
    new_order: CreateBooking
    result: GetJobRequestResponse = GetJobRequestResponse()


class BookingResultRequest(BaseReq):
    job_id: ValidateUUID
    result: GetBookingResponse = GetBookingResponse()
