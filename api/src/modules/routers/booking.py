from modules.queue.booking import BookingHandler
from fastapi import APIRouter, Depends, status
from typing import Annotated
from modules.repository.request_models.booking import (
    CreateBooking,
    CreateBookingRequest,
    BookingResultRequest,
)
from modules.security.dependency import security
from modules.security.current_user import JWTPrincipal
from modules.repository.response_models.job import GetJobRequestResponse, BaseResponse
from modules.repository.response_models.booking import GetBookingResponse
from modules.repository.validators.base import ValidateUUID


class BookingRouter(BookingHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/booking",
            tags=["Bookings"],
        )
        self.router.add_api_route(
            path="/create",
            status_code=status.HTTP_201_CREATED,
            endpoint=self.create_booking,
            response_model=GetJobRequestResponse,
            methods=["POST"],
            description="Register a booking",
        )
        self.router.add_api_route(
            path="/{jobId}",
            status_code=status.HTTP_200_OK,
            endpoint=self.get_booking_result,
            response_model=GetBookingResponse,
            methods=["GET"],
            description="Get booking result",
        )

    async def create_booking(
        self,
        data: CreateBooking,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> BaseResponse:
        return await self._create_booking(
            CreateBookingRequest(new_order=data, credentials=current_user)
        )

    async def get_booking_result(
        self,
        jobId: ValidateUUID,
        current_user: Annotated[
            JWTPrincipal,
            Depends(security),
        ],
    ) -> BaseResponse:
        return await self._get_booking_result(
            BookingResultRequest(job_id=jobId, credentials=current_user)
        )
