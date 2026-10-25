from modules.repository.request_models.base import BaseReq
from modules.repository.response_models.job import (
    GetJobResponse,
    GetJobsResponse,
    CreateJobResponse,
)
from modules.queue.models import Task, JobType
from pydantic import BaseModel, computed_field
from modules.repository.validators.base import ValidateUUID


class GetJobRequest(BaseReq):
    job_id: str
    result: GetJobResponse = GetJobResponse()


class GetJobsRequest(BaseReq):
    result: GetJobsResponse = GetJobsResponse()


class CreateJob(BaseModel):
    id: ValidateUUID

    job_type: JobType = JobType.MANUAL

    tasks: list[Task]

    job_request: dict = {}

    @computed_field
    def number_of_tasks(self) -> str:
        return len(self.tasks)


class CreateJobRequest(BaseReq):
    new_job: CreateJob
    result: CreateJobResponse = CreateJobResponse()
