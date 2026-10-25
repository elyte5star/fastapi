from modules.queue.enums import JobType, ResultType
from modules.repository.request_models.search import CreateSearchRequest
from modules.repository.request_models.search import SearchResultRequest
from modules.repository.response_models.base import BaseResponse
from modules.queue.models import Job, TaskResult
from modules.service.job import JobHandler


class SearchHandler(JobHandler):

    async def _create_search(self, req: CreateSearchRequest) -> BaseResponse:
        if req.credentials is None:
            return req.req_failure("No valid user session found")
        current_user = req.credentials
        job = self._create_job(
            JobType.SEARCH,
            current_user.user_id,
        )
        job.job_request = req.search
        QUEUE = self.cf.queue_names[0]
        success, message = await self._add_job_with_one_task(
            job, QUEUE, ResultType.DATABASE
        )
        if success:
            req.result.job_id = job.id
            return req.req_success(message)
        return req.req_failure(message)

    async def _get_search_result(
        self,
        req: SearchResultRequest,
    ) -> BaseResponse:
        job_id = req.job_id
        job_in_db = await self.find_job_by_id(job_id)
        if job_in_db is None:
            return req.req_failure(f"No job with id::{req.job_id}")
        job = Job.model_validate(job_in_db)
        if job.job_type != JobType.SEARCH:
            return req.req_failure("Wrong job type")
        req.result.job = await self.get_job_response(job)
        if not self.is_job_result_available(job):
            return req.req_failure("No result for job")
        task_id = job_in_db.tasks[0].id
        result_in_db = await self.find_result_by_task_id(task_id)
        if result_in_db is None:
            return req.req_failure("No result in task of job")
        result = TaskResult.model_validate(result_in_db)
        req.result.data = {job.id: (task_id, dict(result))}
        return req.req_success(
            f"Success getting result for job with id: {job_id}.",
        )
