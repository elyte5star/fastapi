from modules.repository.request_models.base import BaseResponse
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


class ProductReview(BaseModel):
    id: str = Field(serialization_alias="rid")
    rating: int
    comment: str
    date: datetime = Field(serialization_alias="createdAt")
    pid: str
    email: str = Field(exclude=True)
    reviewer_name: str = Field(serialization_alias="reviewerName")
    model_config = ConfigDict(from_attributes=True)


class SpecialDeals(BaseModel):
    id: str
    new_price: Decimal = Field(alias="newPrice", exclude=True)
    product_id: str = Field(alias="pid", exclude=True)
    discount: Decimal
    model_config = ConfigDict(from_attributes=True)


class ProductDisplay(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    id: str = Field(serialization_alias="pid")
    created_at: datetime = Field(serialization_alias="createdAt", exclude=True)
    modified_at: Optional[datetime] = Field(
        serialization_alias="modifiedAt", exclude=True
    )
    modified_by: Optional[str] = Field(
        serialization_alias="modifiedBy",
        exclude=True,
    )
    created_by: str = Field(serialization_alias="createdBy", exclude=True)
    type: str = Field(exclude=True)
    name: str
    description: str
    details: str
    image: str
    price: Decimal = Field(max_digits=7, decimal_places=2)
    category: str
    stock_quantity: int = Field(
        serialization_alias="stockQuantity",
    )
    reviews: Optional[list[ProductReview]] = []
    # promotion: Optional[SpecialDeals] = None


class CreateProductResponse(BaseResponse):
    pid: str = ""


class CreateProductsResponse(BaseResponse):
    pids: list[str] = []


class CreateProductReviewResponse(BaseResponse):
    rid: str = ""


class ProductDeals(BaseModel):
    id: str
    new_price: float
    discount: float


class GetProductResponse(BaseResponse):
    product: ProductDisplay | None = None


class GetProductReviewResponse(BaseResponse):
    review: ProductReview | None = None


class GetProductsResponse(BaseResponse):
    products: list[ProductDisplay] = []


class GetProductReviewsResponse(BaseResponse):
    reviews: list[ProductReview] = []
