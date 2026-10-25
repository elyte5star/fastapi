from modules.queue.enums import JobState, ResultType
from modules.queue import models
from modules.queue import schema
from modules.utils.misc import get_indent, date_time_now_utc, time_then
import hashlib
from aio_pika import Message, connect, DeliveryMode
from modules.repository.queries.common import CommonQueries
from typing import Literal


class RQHandler(CommonQueries):

    def create_checksum(self, data: str) -> str:
        digest = hashlib.sha256()
        digest.update(data.encode("utf-8"))
        return digest.hexdigest()

    def validate_checksum(self, data: str, checksum: str) -> bool:
        return self.create_checksum(data) == checksum

    async def _add_job_tasks_to_queue(
        self,
        job: models.Job,
        tasks: list[models.Task],
        results: list[models.TaskResult],
        queue_name: Literal["SEARCH", "BOOKING", "LOST_ITEM", "MANUAL"],
        queue_items: list[models.QueueItem],
    ) -> tuple[bool, str]:
        try:
            # ADD JOB,TASK,RESULT TO DB
            aux_job = job
            aux_job.job_request = (
                job.job_request.model_dump()
                if not isinstance(job.job_request, dict)
                else job.job_request
            )
            new_job = schema.Job(**dict(aux_job))
            _ = await self.add_job_to_db_query(new_job)
            for task, result in zip(tasks, results):
                new_task = schema.Task(**dict(task))
                _ = await self.add_task_to_db_query(new_task)
                new_result = schema.TaskResult(**dict(result))
                _ = await self.add_task_result_db_query(new_result)

            # Perform connection
            connection = await connect(self.cf.amqp_url)

            async with connection:
                # Creating a channel
                channel = await connection.channel()

                # Declaring exchange
                exchange = await channel.declare_exchange(
                    name=self.cf.exchange_name,
                    type=self.cf.exchange_type,
                    auto_delete=True,
                )
                # Declaring queue
                queue = await channel.declare_queue(queue_name, durable=True)

                # Binding queue
                await queue.bind(exchange, queue_name)

                for queue_item in queue_items:
                    # Sending the message
                    await channel.default_exchange.publish(
                        Message(
                            queue_item.model_dump_json(by_alias=True).encode(),
                            delivery_mode=DeliveryMode.PERSISTENT,
                        ),
                        routing_key=queue_name,
                    )
            pass

        except Exception as e:
            self.cf.logger.error(f"Error creating JOB:: {str(e)}")
            return (False, f"Failed to create job. {str(e)}.")
        else:
            return (True, f"Job with id {job.id} created.")

    async def _add_job_with_one_task(
        self,
        job: models.Job,
        queue_name: Literal["SEARCH", "BOOKING", "LOST_ITEM", "MANUAL"],
        result_type: ResultType,
    ) -> tuple[bool, str]:
        job.number_of_tasks = 1
        task = models.Task(
            id=get_indent(),
            job_id=job.id,
            status=models.JobStatus(state=JobState.RECEIVED),
            created_at=date_time_now_utc(),
            finished=time_then(),
        )
        task_result = self.create_task_result(
            result_type,
            task.id,
        )
        queue_items = [
            models.QueueItem(
                job=job,
                task=task,
                result=task_result,
            )
        ]
        success, message = await self._add_job_tasks_to_queue(
            job,
            [task],
            [task_result],
            queue_name,
            queue_items,
        )
        return success, message
