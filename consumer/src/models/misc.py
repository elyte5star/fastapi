import uuid
from datetime import datetime
import logging
import sys

fmt = "%(levelname)s::%(asctime)s::%(name)s::%(funcName)s:%(module)s:logId:%(logId)s::%(message)s"
FORMATTER = logging.Formatter(fmt)

FORMATTER.converter = lambda *args: date_time_now_utc().timetuple()


def time_then() -> datetime:
    return datetime(1971, 1, 1)


def date_time_now_utc() -> datetime:
    return datetime.now()


def get_indent() -> str:
    return str(uuid.uuid4())


class UserFilter(logging.Filter):
    def filter(self, record) -> bool:
        record.logId = get_indent()
        return True


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    console_handler.addFilter(UserFilter())
    return console_handler
