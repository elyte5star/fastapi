from modules.repository.response_models.base import BaseResponse
from modules.repository.response_models.job import JobResponse


class GetSearchResultResponse(BaseResponse):
    job: JobResponse = JobResponse()
    data: dict = {}
