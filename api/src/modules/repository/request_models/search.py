from modules.repository.request_models.base import BaseReq

from pydantic import BaseModel, ConfigDict, Field
from modules.repository.response_models.job import (
    GetJobRequestResponse,
)
from modules.repository.validators.base import ValidateUUID
from modules.repository.response_models.search import GetSearchResultResponse


class Search(BaseModel):
    text: list[str] = []
    categories: list[str] = []
    return_count: int = Field(default=0, serialization_alias="returnCount")
    model_config = ConfigDict(extra="allow")


class CreateSearchRequest(BaseReq):
    search: Search
    result: GetJobRequestResponse = GetJobRequestResponse()


class SaveSearch(BaseModel):
    name: str = ""
    params: Search


class SearchUpdateRequest(SaveSearch):
    search_id: ValidateUUID = Field(validation_alias="searchId")


class SearchResultRequest(BaseReq):
    job_id: ValidateUUID
    result: GetSearchResultResponse = GetSearchResultResponse()
