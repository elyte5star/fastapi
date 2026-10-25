from modules.security.dependency import JWTBearer
from modules.security.current_user import JWTPrincipal
from fastapi import APIRouter, Depends
from modules.repository.request_models.base import (
    GetInfoResponse,
    GetSystemInfoRequest,
    BaseResponse,
    ShutDownAPIRequest,
    GetUUIDStrRequest,
    GetUUIDStrResponse,
)
from typing import Annotated
from modules.service.system import SystemHandler


class SystemInfoRouter(SystemHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/system",
            tags=["System"],
        )
        self.router.add_api_route(
            path="/info",
            endpoint=self.get_system_info,
            response_model=GetInfoResponse,
            methods=["GET"],
        )
        self.router.add_api_route(
            path="/shut_down",
            endpoint=self.shut_down_server,
            response_model=BaseResponse,
            methods=["GET"],
        )

        self.router.add_api_route(
            path="/get_ident",
            endpoint=self.get_ident_str,
            response_model=GetUUIDStrResponse,
            methods=["GET"],
        )

    def get_ident_str(
        self,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ):
        return self._get_ident_str(
            GetUUIDStrRequest(
                credentials=current_user,
            ),
        )

    async def get_system_info(
        self,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ) -> BaseResponse:
        return await self._get_sys_info(
            GetSystemInfoRequest(
                credentials=current_user,
            ),
        )

    async def shut_down_server(
        self,
        current_user: Annotated[
            JWTPrincipal, Depends(JWTBearer(allowed_roles=["ADMIN"]))
        ],
    ) -> BaseResponse:
        return self.shut_down_api(
            ShutDownAPIRequest(
                credentials=current_user,
            ),
        )
