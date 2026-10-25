from fastapi import APIRouter, Depends, status
from typing import Annotated
from modules.queue.search import SearchHandler
from modules.repository.request_models.search import (
    Search,
    CreateSearchRequest,
    SearchResultRequest,
)
from modules.security.dependency import security
from modules.security.current_user import JWTPrincipal
from modules.repository.response_models.base import BaseResponse
from modules.repository.response_models.job import (
    GetJobRequestResponse,
)
from modules.repository.response_models.search import GetSearchResultResponse


class SearchRouter(SearchHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/search",
            tags=["Search"],
        )
        self.router.add_api_route(
            path="/create",
            status_code=status.HTTP_201_CREATED,
            endpoint=self.create_search,
            response_model=GetJobRequestResponse,
            methods=["POST"],
            description="Create search",
        )

        self.router.add_api_route(
            path="/{jobId}",
            endpoint=self.get_search_result,
            response_model=GetSearchResultResponse,
            methods=["GET"],
            description="Get search result",
        )

    async def create_search(
        self,
        data: Search,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> BaseResponse:
        return await self._create_search(
            CreateSearchRequest(search=data, credentials=current_user)
        )

    async def get_search_result(
        self,
        jobId: str,
        current_user: Annotated[
            JWTPrincipal,
            Depends(security),
        ],
    ) -> BaseResponse:
        return await self._get_search_result(
            SearchResultRequest(job_id=jobId, credentials=current_user)
        )
