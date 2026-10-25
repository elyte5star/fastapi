import logging
import sys
import os
from logging.handlers import (
    TimedRotatingFileHandler,
    SMTPHandler,
    QueueHandler,
)
from os import path, getenv
from pathlib import Path
from modules.settings.configuration import ApiConfig
from modules.utils.misc import get_indent, date_time_now_utc
import json
from multiprocessing import Queue

base_dir = Path(__file__).parent.parent.parent.parent.parent
logs_target = path.join(base_dir / "logs", "api.log")
logs_error_target = path.join(base_dir / "logs", "error.log")

# Ensure log directory exists
os.makedirs(os.path.dirname(logs_target), exist_ok=True)
# Ensure log directory exists
os.makedirs(os.path.dirname(logs_error_target), exist_ok=True)


fmt = "%(levelname)s::%(asctime)s::%(name)s::%(funcName)s:%(module)s:currentUser:%(currentUser)s::logId:%(logId)s::%(message)s"


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
            "time": self.formatTime(record, self.datefmt),
            "function": record.funcName,
            "currentUser": str(getenv("current_user", "API")),
            "logId": get_indent(),
            "filename": record.filename,
            "module": record.module,
        }
        return json.dumps(log_record, sort_keys=True)


class QueueLoggingHandler(QueueHandler):
    def __init__(self, queue: Queue) -> None:
        super().__init__(queue)

    def emit(self, record: logging.LogRecord) -> None:
        return super().emit(record)

    def close(self) -> None:
        return super().close()


class UserFilter(logging.Filter):
    def filter(self, record) -> bool:
        record.currentUser = str(getenv("current_user", "API"))
        record.logId = get_indent()
        return True


FORMATTER = logging.Formatter(fmt)

FORMATTER.converter = lambda *args: date_time_now_utc().timetuple()


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    console_handler.addFilter(UserFilter())
    return console_handler


def smtp_log_handler(cfg: ApiConfig):
    smtp_handler = SMTPHandler(
        mailhost=(cfg.mail_server, cfg.mail_port),
        fromaddr=cfg.email,
        toaddrs=["elyte5star@gmail.com"],
        subject="Exceptional Log",
        credentials=(cfg.mail_username, cfg.mail_password),
        secure=None,
    )
    smtp_handler.setFormatter(JSONFormatter())
    smtp_handler.setLevel(logging.CRITICAL)
    return smtp_handler


def info_file_handler(filename: str = logs_target):
    file_handler = TimedRotatingFileHandler(filename, when="midnight")
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.INFO)
    return file_handler


def error_file_handler(filename: str = logs_error_target):
    file_handler = TimedRotatingFileHandler(filename, when="midnight")
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.WARNING)
    return file_handler
