from modules.service.job import JobHandler
from fastapi import APIRouter, Depends, status
from modules.security.dependency import security, JWTBearer
from modules.security.current_user import JWTPrincipal
from modules.repository.request_models.job import (
    GetJobRequest,
    GetJobsRequest,
    CreateJobRequest,
    CreateJob,
)
from modules.repository.response_models.job import (
    GetJobResponse,
    GetJobsResponse,
    CreateJobResponse,
    BaseResponse,
)
from typing_extensions import Annotated
from modules.queue.models import Job
from modules.repository.validators.base import ValidateUUID


class JobRouter(JobHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(prefix="/job", tags=["Job"])
        self.router.add_api_route(
            path="/create",
            status_code=status.HTTP_201_CREATED,
            endpoint=self.create_job,
            response_model=CreateJobResponse,
            methods=["POST"],
            description="Create a Job",
        )

        self.router.add_api_route(
            path="/{jobId}",
            endpoint=self.get_job,
            response_model=GetJobResponse,
            methods=["GET"],
            description="Get Job Status",
        )

        self.router.add_api_route(
            path="",
            endpoint=self.get_jobs,
            response_model=GetJobsResponse,
            methods=["GET"],
            description="Get Jobs, Admin right required",
        )

    async def get_jobs(
        self,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ) -> BaseResponse:
        return await self._get_jobs(GetJobsRequest(credentials=current_user))

    async def get_job(
        self,
        jobId: ValidateUUID,
        current_user: Annotated[
            JWTPrincipal,
            Depends(security),
        ],
    ) -> BaseResponse:
        return await self._get_job(
            GetJobRequest(credentials=current_user, job_id=jobId)
        )

    async def create_job(
        self,
        job: CreateJob,
        current_user: Annotated[
            JWTPrincipal,
            Depends(security),
        ],
    ):
        return await self._create_new_job(
            CreateJobRequest(new_job=job, credentials=current_user)
        )
