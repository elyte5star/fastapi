from modules.repository.request_models.job import (
    GetJobRequest,
    CreateJobRequest,
    GetJobsRequest,
)
from modules.repository.response_models.job import JobResponse, BaseResponse
from datetime import datetime
from modules.queue.enums import JobState, JobType, ResultType, ResultState
from modules.utils.misc import time_then, get_indent, date_time_now_utc
from modules.queue.models import TaskResult, QueueItem
from modules.queue.base import RQHandler
from modules.queue.models import Job


class JobHandler(RQHandler):
    def __init__(self, config):
        super().__init__(config)
        self.jobs = {}

    async def _get_job(self, req: GetJobRequest) -> BaseResponse:
        job_in_db = await self.find_job_by_id(req.job_id)
        if job_in_db is None:
            return req.req_failure(f"No job with id::{req.job_id}")
        job = Job.model_validate(job_in_db)
        req.result.job_status = await self.get_job_response(job)
        return req.req_success(
            f"Success getting status for job with id: {req.job_id}.",
        )

    async def _get_jobs(self, req: GetJobsRequest) -> BaseResponse:
        jobs_in_db = await self.get_jobs_query()
        jobs_status = [
            await self.get_job_response(Job.model_validate(job_in_db))
            for job_in_db in jobs_in_db
        ]
        req.result.jobs_status = jobs_status
        return req.req_success(
            f"{len(jobs_status)} found!",
        )

    async def get_job_response(self, job: Job) -> JobResponse:
        states, successes, stops = ([], [], [])
        tasks_exist = False
        tasks = await self.find_tasks_by_job_id(job.id)
        for task in tasks:
            tasks_exist = True
            states.append(task.status.state)
            successes.append(task.status.success)
            stops.append(task.finished)
        if not tasks_exist:
            job.job_status.state = JobState.NOTASKS
            job.job_status.success = False
            job.job_status.is_finished = True
            return self.create_job_response(job)

        stops.sort()
        success = True
        state = JobState.FINISHED
        is_finished = True

        if JobState.TIMEOUT in states:
            state = JobState.TIMEOUT
            success = False
            is_finished = True
        elif JobState.NOTSET in states:
            state = JobState.NOTSET
            success = False
            is_finished = False
        elif JobState.RECEIVED in states:
            state = JobState.PENDING
            success = False
            is_finished = False
        elif JobState.PENDING in states:
            state = JobState.PENDING
            success = False
            is_finished = False

        job.job_status.state = state
        job.job_status.success = success
        job.job_status.is_finished = is_finished
        return self.create_job_response(job, stops[-1])

    def create_job_response(
        self, job: Job, stopped: datetime = time_then()
    ) -> JobResponse:
        return JobResponse(
            user_id=job.user_id,
            start_time=job.created_at,
            stop_time=stopped,
            job_type=job.job_type,
            job_id=job.id,
            job_status=job.job_status,
            process_time=float((stopped - job.created_at).total_seconds()),
        )

    def is_job_result_available(self, job: Job) -> bool:
        if job.job_status.is_finished is False:
            return False
        if job.job_status.state != JobState.FINISHED:
            return False
        return job.job_status.success

    def _create_job(self, job_type: JobType, user_id: str) -> Job:
        job = Job()
        job.user_id = user_id
        job.job_type = job_type
        job.id = get_indent()
        job.job_status.state = JobState.PENDING
        job.created_at = date_time_now_utc()
        job.created_by = user_id
        return job

    async def _create_new_job(self, req: CreateJobRequest):
        if req.credentials is None:
            return req.req_failure("No valid user session found")
        job = self._create_job(req.new_job.job_type, req.credentials.user_id)
        job.tasks = req.new_job.tasks
        job.id = req.new_job.id
        number_of_tasks = req.new_job.number_of_tasks
        job.number_of_tasks = number_of_tasks
        job.job_request = req.new_job.job_request
        if number_of_tasks < 1:
            return req.req_failure("No tasks in job")
        queue_items: list[QueueItem] = []
        tasks_results: list[TaskResult] = []
        for task in job.tasks:
            task.status.state = JobState.RECEIVED
            task.created_at = date_time_now_utc()
            task.finished = time_then()
            task_result = self.create_task_result(ResultType.UNKNOWN, task.id)
            tasks_results.append(task_result)
            queue_items.append(
                QueueItem(job=job, task=task, result=task_result),
            )
        QUEUE = self.cf.queue_names[3]
        success, message = await self._add_job_tasks_to_queue(
            job,
            job.tasks,
            tasks_results,
            QUEUE,
            queue_items,
        )
        if success:
            req.result.job = job
            return req.req_success(message)
        return req.req_failure(message)

    def create_task_result(
        self,
        result_type: ResultType,
        task_id: str,
    ) -> TaskResult:
        return TaskResult(
            id=get_indent(),
            task_id=task_id,
            result_type=result_type,
            result_state=ResultState.PENDING,
        )
