import time
from modules.utils.misc import get_indent
from modules.repository.response_models.base import (
    BaseResponse,
    GetInfoResponse,
    GetUUIDStrResponse,
)
from pydantic import BaseModel, ConfigDict
from modules.security.current_user import JWTPrincipal


class BaseReq(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    credentials: JWTPrincipal | None = None

    def model_post_init(self, ctx):
        self.result: BaseResponse = BaseResponse()
        self.result.req_id = get_indent()
        self.result.start_time = time.perf_counter()

    def req_success(self, message: str = "") -> BaseResponse:
        self.result.success = True
        if message:
            self.result.message = message
        self.req_process_time()
        return self.result

    def is_cred_expired(self) -> bool:
        if self.credentials:
            if time.time() > self.credentials.expires:
                return True
        return False

    def req_failure(self, message: str = "") -> BaseResponse:
        self.result.success = False
        if message:
            self.result.message = message
        self.req_process_time()
        return self.result

    def req_process_time(self):
        self.result.stop_time = time.perf_counter()
        self.result.process_time = (
            f"{(self.result.stop_time - self.result.start_time):.4f} seconds"
        )


class GetSystemInfoRequest(BaseReq):
    result: GetInfoResponse = GetInfoResponse()


class ShutDownAPIRequest(BaseReq):
    result: BaseResponse = BaseResponse()


class GetUUIDStrRequest(BaseReq):
    result: GetUUIDStrResponse = GetUUIDStrResponse()
