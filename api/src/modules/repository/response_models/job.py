from pydantic import Field, BaseModel, field_serializer
from datetime import datetime
from modules.queue.enums import JobType
from modules.queue.models import Job, JobStatus
from modules.repository.request_models.base import BaseResponse
from modules.utils.misc import time_then


class JobResponse(BaseModel):
    user_id: str = Field(default="", serialization_alias="userId")
    start_time: datetime = Field(
        default=time_then(),
        serialization_alias="startTime",
    )
    stop_time: datetime = Field(
        default=time_then(),
        serialization_alias="stopTime",
    )
    process_time: float = Field(default=0.0, serialization_alias="processTime")
    job_type: JobType = Field(
        default=JobType.EMPTY,
        serialization_alias="jobType",
    )
    job_id: str = Field(default="", serialization_alias="jobId")
    job_status: JobStatus = Field(
        default=JobStatus(),
        serialization_alias="jobStatus",
    )

    @field_serializer("job_type")
    def serialize_job_type(self, job_type: JobType) -> str:
        return job_type.name


class GetJobsResponse(BaseResponse):
    jobs_status: list[JobResponse] = []


class GetJobResponse(BaseResponse):
    job_status: JobResponse | None = Field(
        default=None, serialization_alias="jobResponse"
    )


class CreateJobResponse(BaseResponse):
    job: Job | None = None


class GetJobRequestResponse(BaseResponse):
    job_id: str = Field(default="", serialization_alias="jobId")
