from models.base import SearchModel, QueueItem

from psycopg.connection import Connection


class SearchHandler:

    def __init__(self, queue_item: QueueItem, db_conn: Connection) -> None:
        self.queue_item = queue_item
        self.db_conn = db_conn

    def handle(self) -> tuple[bool, dict]:
        search_request: SearchModel = self.queue_item.job.job_request
        return (False, {})

    def query_generation(self, search_request: SearchModel):

        pass

    def search(self, params: dict) -> dict:
        return {}
