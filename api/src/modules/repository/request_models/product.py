from pydantic import BaseModel, Field, computed_field
from typing_extensions import Annotated
from modules.repository.request_models.base import BaseReq
from modules.repository.response_models.product import (
    CreateProductResponse,
    CreateProductsResponse,
    GetProductResponse,
    GetProductsResponse,
    CreateProductReviewResponse,
    GetProductReviewsResponse,
    GetProductReviewResponse,
    BaseResponse,
)
from modules.repository.validators.base import VerifyEmail, ValidateUUID
from decimal import Decimal
from modules.utils.misc import get_indent


class CreateProduct(BaseModel):
    name: str
    description: str
    details: str
    image: str
    price: Decimal = Field(max_digits=7, decimal_places=2)
    category: str
    stock_quantity: Annotated[
        int,
        Field(
            examples=[1, 3, 4],
            default=1,
            strict=True,
            gt=0,
            validation_alias="stockQuantity",
        ),
    ]

    @computed_field
    def id(self) -> str:
        return get_indent()


class CreateProductReview(BaseModel):
    rating: int = Field(ge=0, le=5)
    comment: str = Field(min_length=3, max_length=500)
    email: VerifyEmail
    pid: ValidateUUID
    reviewer_name: Annotated[
        str,
        Field(strict=True, validation_alias="reviewerName"),
    ]

    @computed_field
    def id(self) -> str:
        return get_indent()


class DeleteProductRequest(BaseReq):
    pid: ValidateUUID
    result: BaseResponse = BaseResponse()


class CreateProductReviewRequest(BaseReq):
    review: CreateProductReview
    result: CreateProductReviewResponse = CreateProductReviewResponse()


class CreateProductsRequest(BaseReq):
    new_products: list[CreateProduct] = []
    result: CreateProductsResponse = CreateProductsResponse()


class CreateProductRequest(BaseReq):
    new_product: CreateProduct
    result: CreateProductResponse = CreateProductResponse()


class GetProductRequest(BaseReq):
    pid: ValidateUUID
    result: GetProductResponse = GetProductResponse()


class GetProductReviewRequest(BaseReq):
    rid: ValidateUUID
    result: GetProductReviewResponse = GetProductReviewResponse()


class GetProductsRequest(BaseReq):
    result: GetProductsResponse = GetProductsResponse()


class GetProductReviewsRequest(BaseReq):
    result: GetProductReviewsResponse = GetProductReviewsResponse()
