from datetime import datetime, timedelta
from pytz import timezone
import uuid
from fastapi.encoders import jsonable_encoder
import string
import secrets
import bcrypt
from decimal import Decimal
from json import JSONEncoder
from starlette.requests import Request
import random
import sys
import time


# Request limiter algorithm
class TokenBucket:
    def __init__(self, tokens: int, refill_rate: int) -> None:
        self.tokens = tokens
        self.refill_rate = refill_rate
        self.bucket = tokens
        self.last_refill = time.perf_counter()

    def check(self) -> bool:
        current = time.perf_counter()
        time_passed = current - self.last_refill
        self.last_refill = current
        self.bucket = self.bucket + time_passed * (self.tokens / self.refill_rate)
        if self.bucket > self.tokens:
            self.bucket = self.tokens
        if self.bucket < 1:
            return False
        self.bucket = self.bucket - 1
        return True


def date_time_now_local_tz() -> datetime:
    return datetime.now().astimezone(timezone("Europe/Stockholm"))


def date_time_now_utc_tz() -> datetime:
    return datetime.now().astimezone(timezone("UTC"))


def time_then() -> datetime:
    return datetime(1971, 1, 1)


def date_time_now_utc() -> datetime:
    return datetime.now()


def get_indent() -> str:
    return str(uuid.uuid4())


def time_delta(minutes: int) -> timedelta:
    return timedelta(minutes=minutes)


def obj_as_json(obj):
    return jsonable_encoder(obj)


def debug_var(var):
    sys.stderr.write(str(var))
    sys.stderr.write("\n")


def get_client_ip_address(request: Request) -> str:
    xf_header = request.headers.get("X-Forwarded-For")
    if xf_header is not None:
        return xf_header.split(",")[0]
    # return "128.101.101.101"  # for testing Richfield,United States
    # return "41.238.0.198"  # for testing Giza, Egypt
    return request.client.host if request.client else ""


def _get_x_correlation_id() -> str:
    size = 12
    chars = string.digits
    correlation_id = "".join(random.choice(chars) for _ in range(size)) + "_SC"
    return correlation_id


class DecimalEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return (str(o) for o in [o])
        return super(DecimalEncoder, self).default(o)


# class ObjIDEncoder(JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, ObjectId):
#             return str(obj)
#         return super(ObjIDEncoder, self).default(obj)


def hash_password(plain_password: str, salt: int, encoding: str) -> str:
    hashed_password = bcrypt.hashpw(
        plain_password.encode(encoding), bcrypt.gensalt(salt)
    ).decode(encoding)
    return hashed_password


def create_password(size: int, salt: int, encoding: str) -> tuple[str, str]:
    chars = (
        string.digits
        + string.ascii_letters
        + string.punctuation.replace("'", "").replace('"', "")
    )
    plain_password = "".join(secrets.choice(chars) for _ in range(size))
    hashed_password = hash_password(plain_password, salt, encoding)
    return (plain_password, hashed_password)


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


class AsyncIteratorWrapper:
    """The following is a utility class that transforms a
    regular iterable to an asynchronous one.

    link: https://www.python.org/dev/peps/pep-0492/#example-2
    """

    def __init__(self, obj):
        self._it = iter(obj)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            value = next(self._it)
        except StopIteration:
            raise StopAsyncIteration
        return value


# def random_date(self, start_date, range_in_days):
#     days_to_add = np.arange(0, range_in_days)
#     rd = np.datetime64(start_date) + np.random.choice(days_to_add)
#     return str(rd)
