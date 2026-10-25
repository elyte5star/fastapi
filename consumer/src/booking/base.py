from models.base import QueueItem, BookingModel
from psycopg.connection import Connection
from models.misc import get_indent, date_time_now_utc
from psycopg.types.json import Jsonb


class BookingHandler:

    def __init__(self, queue_item: QueueItem, db_conn: Connection) -> None:
        self.queue_item = queue_item
        self.db_conn = db_conn

    def handle(self) -> tuple[bool, dict]:
        payload = self.queue_item.job.job_request
        booking_request: BookingModel = payload
        cart = [cart_item.model_dump_json() for cart_item in booking_request.cart]
        result = {}
        with self.db_conn.cursor() as cur:
            stm = """INSERT INTO booking (id, user_id,cart,address,created_at,
            total_price) VALUES (%s, %s,%s, %s,%s, %s) RETURNING id """
            data = (
                get_indent(),
                booking_request.user_id,
                cart,
                booking_request.shipping_address.model_dump_json(
                    by_alias=True,
                ),
                date_time_now_utc(),
                booking_request.total_price,
            )
            cur.execute(stm, data)
            row = cur.fetchone()
            result["bookingId"] = row["id"]
            result["jobId"] = self.queue_item.job.id
            result["taskId"] = self.queue_item.task.id
            # Make the changes to the database persistent
            self.db_conn.commit()
        return (True, result)
