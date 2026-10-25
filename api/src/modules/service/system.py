from modules.repository.queries.common import CommonQueries
from modules.repository.request_models.base import (
    BaseResponse,
    GetSystemInfoRequest,
    ShutDownAPIRequest,
    GetUUIDStrRequest,
)

import os
import signal
from modules.utils.misc import get_indent


class SystemHandler(CommonQueries):
    async def _get_sys_info(
        self,
        req: GetSystemInfoRequest,
    ) -> BaseResponse:
        if req.credentials is None:
            return req.req_failure("No valid user session found")
        info = await self.system_info()
        info["currentUser"] = req.credentials.model_dump(by_alias=True)
        req.result.info = info
        self.logger.info(f"{req.credentials.username} checked the system")
        return req.req_success("System information")

    def shut_down_api(self, req: ShutDownAPIRequest) -> BaseResponse:
        if req.credentials is None:
            return req.req_failure("No valid user session found")
        current_user = req.credentials
        self.logger.warning(f"{current_user.username} shut down server")
        os.kill(os.getpid(), signal.SIGTERM)
        return req.req_success("Server shutting down...'")

    def _get_ident_str(self, req: GetUUIDStrRequest) -> BaseResponse:
        if req.credentials is None:
            return req.req_failure("No valid user session found")
        req.result.id = get_indent()
        return req.req_success("Success getting UUID")
