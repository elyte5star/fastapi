from pydantic import BaseModel, Field, ConfigDict, AfterValidator
from datetime import datetime
from typing_extensions import Annotated
import uuid
from models.enums import (
    JobState,
    JobType,
    ResultState,
    ResultType,
    WorkerType,
)
from models.misc import date_time_now_utc


def check_uuid(value: str) -> str:
    try:
        val = uuid.UUID(value, version=4)
        return str(val)
    except Exception:
        print(f"{value} is an invalid id")
        raise SystemExit


ValidateUUID = Annotated[str, AfterValidator(check_uuid)]


class CartItem(BaseModel):
    price: float = Field(
        repr=True,
        gt=0,
    )
    discount: float
    quantity: Annotated[
        int,
        Field(
            examples=[1, 3, 4],
            strict=True,
            repr=True,
            gt=0,
        ),
    ]
    pid: ValidateUUID

    calculated_price: str


class ShippingAddress(BaseModel):
    first_name: Annotated[
        str,
        Field(
            validation_alias="firstName",
            serialization_alias="firstName",
        ),
    ]
    last_name: Annotated[
        str, Field(validation_alias="lastName", serialization_alias="lastName")
    ]
    street_address: Annotated[
        str,
        Field(
            validation_alias="streetAddress",
            serialization_alias="streetAddress",
        ),
    ]
    country: str
    state: str
    email: str
    zip_code: Annotated[
        str,
        Field(
            validation_alias="zipCode",
            serialization_alias="zipCode",
        ),
    ]
    model_config = ConfigDict(extra="forbid")


class BookingModel(BaseModel):
    cart: list[CartItem]
    total_price: Annotated[
        str,
        Field(
            serialization_alias="totalPrice",
        ),
    ]
    shipping_address: Annotated[
        ShippingAddress,
        Field(
            serialization_alias="shippingAddress",
        ),
    ]
    user_id: str = Field(serialization_alias="userId")
    model_config = ConfigDict(from_attributes=True)


class SearchModel(BaseModel):
    text: list[str] = []
    categories: list[str] = []
    return_count: int = Field(default=0, serialization_alias="returnCount")
    model_config = ConfigDict(extra="allow")


class JobStatus(BaseModel):
    state: JobState = JobState.NOTSET
    success: bool = False
    is_finished: bool = Field(default=False, serialization_alias="isFinished")


class TaskResult(BaseModel):
    id: str = Field(validation_alias="resultId")
    result_type: ResultType
    result_state: ResultState
    task_id: str = Field(validation_alias="taskId")
    data: dict = {}
    data_checksum: str | None = Field(
        default=None,
        serialization_alias="dataChecksum",
    )

    model_config = ConfigDict(from_attributes=True)


class Task(BaseModel):
    id: str = Field(validation_alias="taskId")
    job_id: str = Field(validation_alias="jobId")
    status: JobStatus = JobStatus()
    item: dict = {}
    created_at: datetime | None = Field(
        default=None,
        validation_alias="createdAt",
    )

    started: datetime | None = None
    finished: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Job(BaseModel):
    id: str = Field(default="", validation_alias="jobId")
    user_id: str = Field(default="", validation_alias="userId")
    job_type: JobType = Field(
        default=JobType.EMPTY,
        validation_alias="jobType",
    )
    created_at: datetime = Field(validation_alias="createdAt")
    job_status: JobStatus = Field(
        default=JobStatus(),
        validation_alias="jobStatus",
    )
    tasks: list[Task] = []
    number_of_tasks: int = Field(
        default=0,
        validation_alias="numberOfTasks",
    )
    job_request: BookingModel | SearchModel | dict = Field(
        default={},
        validation_alias="jobRequest",
    )

    created_by: str = Field(default="", validation_alias="createdBy")

    model_config = ConfigDict(from_attributes=True)


class ResultLog(BaseModel):
    result_id: str
    created_at: datetime
    handled: bool = False
    handled_date: datetime | None = Field(
        default=None,
        serialization_alias="handledDate",
    )


class QueueItem(BaseModel):
    job: Job
    task: Task
    result: TaskResult


class Worker(BaseModel):
    id: ValidateUUID = Field(default="", serialization_alias="workerId")
    worker_type: WorkerType = Field(
        default=WorkerType.NONE, serialization_alias="workerType"
    )
    queue_name: str = Field(default="")
    created_at: datetime = Field(
        default=date_time_now_utc(), serialization_alias="createdAt"
    )
    queue_host: str = Field(default="")
    process_id: str | None = Field(default=None, serialization_alias="processId")

    model_config = ConfigDict(from_attributes=True)
