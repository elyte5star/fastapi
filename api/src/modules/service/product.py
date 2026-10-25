from modules.repository.queries.product import ProductQueries
from modules.repository.request_models.product import (
    CreateProductRequest,
    GetProductRequest,
    GetProductsRequest,
    CreateProductsRequest,
    CreateProductReviewRequest,
    GetProductReviewRequest,
    DeleteProductRequest,
)
from modules.repository.response_models.product import (
    BaseResponse,
    ProductDisplay,
    ProductReview,
)
from modules.database.schema.product import Product, Review


class ProductHandler(ProductQueries):

    async def _create_product(
        self,
        req: CreateProductRequest,
    ) -> BaseResponse:
        if req.credentials is None:
            return req.req_failure("No valid user session found")
        product_exist = await self.find_product_by_name(req.new_product.name)
        current_user = req.credentials
        if product_exist is None:
            new_product = Product(
                **req.new_product.model_dump(),
                **dict(created_by=current_user.user_id),
            )
            await self.create_product_query(new_product)
            req.result.pid = new_product.id
            return req.req_success(
                f"Product with id: {new_product.id} created",
            )
        return req.req_failure("Product already exist")

    async def _create_many_products(
        self,
        req: CreateProductsRequest,
    ) -> BaseResponse:
        if req.credentials is None:
            return req.req_failure("No valid user session found")
        current_user = req.credentials
        new_products, product_ids = [], []
        for new_product in req.new_products:
            product_exist = await self.find_product_by_name(new_product.name)
            if product_exist is None:
                new_product = Product(
                    **new_product.model_dump(),
                    **dict(created_by=current_user.user_id),
                )
                product_ids.append(new_product.id)
                new_products.append(new_product)
            else:
                self.cf.logger.warning(
                    f"product with name: {product_exist.name} exist",
                )

        await self.create_products_query(new_products)
        req.result.pids = product_ids
        return req.req_success(
            f"Total number of products created: {len(new_products)}",
        )

    async def _create_review(
        self,
        req: CreateProductReviewRequest,
    ) -> BaseResponse:
        product = await self.find_product_by_id(req.review.pid)
        if product is not None:
            new_review = Review(**req.review.model_dump())
            await self.create_product_review_query(new_review)
            req.result.rid = new_review.id
            return req.req_success(
                f"Product review with id: {new_review.id} created",
            )
        return req.req_failure(f"Product with pid {req.review.pid} not found")

    async def _get_product(self, req: GetProductRequest) -> BaseResponse:
        product_in_db = await self.find_product_by_id(req.pid)
        if product_in_db is not None:
            pydantic_model = ProductDisplay.model_validate(product_in_db)
            req.result.product = pydantic_model
            return req.req_success(f"Product with pid {req.pid} found")
        return req.req_failure(f"Product with pid {req.pid} not found")

    async def _get_product_review(
        self,
        req: GetProductReviewRequest,
    ) -> BaseResponse:
        review_in_db = await self.find_product_review_by_id(req.rid)
        if review_in_db is not None:
            pydantic_model = ProductReview.model_validate(review_in_db)
            req.result.review = pydantic_model
            return req.req_success(f"Product review with rid {req.rid} found")
        return req.req_failure(f"Product with review rid {req.rid} not found")

    async def _get_products(
        self,
        req: GetProductsRequest,
    ) -> BaseResponse:
        products_in_db = [
            ProductDisplay.model_validate(product_in_db)
            for product_in_db in await self.get_products_query()
        ]
        req.result.products = products_in_db
        return req.req_success(f"Total number of products: {len(products_in_db)}")

    async def _delete_product(self, req: DeleteProductRequest) -> BaseResponse:
        if req.credentials is None:
            return req.req_failure("No valid user session found")
        current_user = req.credentials
        product = await self.find_product_by_id(req.pid)
        if product is not None:
            await self.delete_product_query(req.pid)
            self.cf.logger.warning(
                f"Product with id: {req.pid} was deleted by:: {current_user.user_id}"
            )
            return req.req_success(f"Product with id: {req.pid} deleted")
        return req.req_failure(f"Product with pid {req.pid} not found")
