from multiprocessing import Process
from booking.base import BookingHandler
from search.base import SearchHandler
from rabbitmq.base import Queue
from config.settings import AppConfig
from models.enums import WorkerType, JobType, JobState, ResultState
from models.misc import get_indent, date_time_now_utc
from models.base import TaskResult, Worker, QueueItem, Task, Job
import psycopg
import json
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties
from pika.spec import Basic
from psycopg.types.json import Jsonb
from psycopg.rows import dict_row
from typing import Literal


class Consumer(Process):

    def __init__(
        self,
        config: AppConfig,
        worker_type: WorkerType,
        queue: Literal["SEARCH", "BOOKING", "LOST_ITEM", "MANUAL"],
        routing_key: str,
    ) -> None:
        super().__init__()
        self.cfg = config
        self.worker_type = worker_type
        self.queue: Literal["SEARCH", "BOOKING", "LOST_ITEM", "MANUAL"] = queue
        self.routing_key = routing_key

    def create_worker(self) -> Worker:
        worker = Worker()
        worker.id = get_indent()
        worker.worker_type = self.worker_type
        worker.queue_name = self.queue
        worker.queue_host = self.cfg.amqp_url
        worker.process_id = str(self.pid)
        return worker

    def db_conn(self):
        try:
            conn = psycopg.connect(self.cfg.database_url, row_factory=dict_row)
            return conn
        except psycopg.errors.DatabaseError as e:
            print(e)
            raise

    def insert_worker_into_db(self, worker: Worker):
        with self.db_conn() as conn:
            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                stm = """INSERT INTO worker (id, worker_type,created_at,
                        queue_name,queue_host,
                        process_id) VALUES (%s, %s,%s, %s,%s, %s)"""
                data = (
                    worker.id,
                    worker.worker_type.name,
                    worker.created_at,
                    worker.queue_name,
                    worker.queue_host,
                    worker.process_id,
                )
                cur.execute(stm, data)
                # Make the changes to the database persistent
                conn.commit()

    def update_on_going_tasks_in_db(self, task_id: str):
        with self.db_conn() as conn:
            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                stm = "UPDATE task SET status= %s,started= %s WHERE id= %s"
                status = {
                    "state": JobState.PENDING,
                    "success": False,
                    "is_finished": False,
                }
                data = (Jsonb(status), date_time_now_utc(), task_id)
                cur.execute(stm, data)
                # Make the changes to the database persistent
                conn.commit()

    def update_finished_tasks_in_db(self, task_id: str, success: bool):
        with self.db_conn() as conn:
            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                stm = "UPDATE task SET status= %s,finished= %s WHERE id= %s"
                status = {
                    "state": JobState.FINISHED,
                    "success": success,
                    "is_finished": True,
                }
                data = (Jsonb(status), date_time_now_utc(), task_id)
                cur.execute(stm, data)
                # Make the changes to the database persistent
                conn.commit()

    def update_result(self, result_id: str, data: dict):
        with self.db_conn() as conn:
            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                stm = "UPDATE taskresult SET result_state= %s,data= %s WHERE id= %s"
                # data_json = json.dumps(data, indent=4, sort_keys=True, default=str)
                values = (ResultState.PRESENT.name, Jsonb(data), result_id)
                cur.execute(stm, values)
                # Make the changes to the database persistent
                conn.commit()

    def call_back(
        self,
        channel: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body,
    ) -> None:
        # Get job and task from queue item.
        try:
            received = body.decode()
            queue_item_dict = json.loads(received)
            queue_item = QueueItem(**queue_item_dict)
            self.cfg.logger.info(f"[x] Received job with id: {queue_item.job.id}")
            self.do_work(queue_item)
            self.cfg.logger.info(" [x] Done")
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self.cfg.logger.error(f"[+] Error doing work: {e}")

    def do_work(self, queue_item: QueueItem):
        try:
            task: Task = queue_item.task
            result: TaskResult = queue_item.result
            job: Job = queue_item.job
            success = False
            data = {}
            self.update_on_going_tasks_in_db(task.id)
            match job.job_type:
                case JobType.EMPTY:
                    raise SystemExit("No job on the queue")
                case JobType.SEARCH:
                    search = SearchHandler(queue_item, self.db_conn())
                    success, data = search.handle()
                case JobType.BOOKING:
                    booking = BookingHandler(queue_item, self.db_conn())
                    success, data = booking.handle()
                case JobType.MANUAL:
                    self.cfg.logger.info("Not Implemented")
                case _:
                    pass
                    # raise SystemExit(f"Unknown job type: {job.job_type}")

        except Exception as e:
            queue: Queue = Queue(self.cfg)
            queue.create_exchange(
                self.cfg.queue_names[2],
                self.cfg.exchange_name,
                self.cfg.exchange_type,
                self.cfg.queue_names[2],
            )
            queue.send_message(
                self.cfg.queue_names[2],
                self.cfg.queue_names[2],
                queue_item.model_dump_json(by_alias=True).encode(),
            )
            # queue.close_connection()
            self.cfg.logger.error(f"[+] Consumer Exception: {e}")
        finally:
            self.update_finished_tasks_in_db(task.id, success)
            self.update_result(result.id, data)

    def run(self) -> None:
        queue: Queue = Queue(self.cfg)
        queue.create_exchange(
            self.queue,
            self.cfg.exchange_name,
            self.cfg.exchange_type,
            self.routing_key,
        )
        self.insert_worker_into_db(self.create_worker())
        queue.listen_to_queue(self.queue, self.call_back)
