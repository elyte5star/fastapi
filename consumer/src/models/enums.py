from enum import Enum


class WorkerType(str, Enum):
    NONE = "0"
    BOOKING = "1"
    SEARCH = "2"
    GENERIC = "3"


class JobType(str, Enum):
    EMPTY = "0"
    SEARCH = "10"
    BOOKING = "30"
    MANUAL = "40"


class JobState(str, Enum):
    NOTSET = "0"
    RECEIVED = "10"
    PENDING = "20"
    FINISHED = "30"
    TIMEOUT = "666"
    NOTASKS = "999"


class ResultState(str, Enum):
    NOTSET = "0"
    PENDING = "10"
    PRESENT = "20"
    ARCHIVED = "30"
    REMOVED = "40"


class ResultType(str, Enum):
    UNKNOWN = "0"
    DATABASE = "10"
    FILE = "30"
