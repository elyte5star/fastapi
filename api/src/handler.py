from modules.settings.configuration import ApiConfig
from fastapi.logger import logger
from modules.routers.auth import AuthRouter
from modules.routers.search import SearchRouter
from modules.routers.user import UserRouter
from modules.routers.product import ProductRouter
from modules.routers.booking import BookingRouter
from modules.routers.job import JobRouter
from modules.routers.system import SystemInfoRouter
from fastapi import APIRouter, status
from sqlalchemy.engine import Engine
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy import event
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


cfg = ApiConfig().from_toml_file().from_env_file()

cfg.logger = logger


system_router = SystemInfoRouter(cfg)

auth_router = AuthRouter(cfg)

user_router = UserRouter(cfg)

product_router = ProductRouter(cfg)

booking_router = BookingRouter(cfg)

search_router = SearchRouter(cfg)

job_router = JobRouter(cfg)


routes: tuple[APIRouter, ...] = (
    system_router.router,
    auth_router.router,
    user_router.router,
    product_router.router,
    booking_router.router,
    search_router.router,
    job_router.router,
)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    logger.error(f"{repr(exc.detail)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": str(exc.detail),
            "success": False,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": " ".join(exc.errors()),
            "body": exc.body,
            "success": False,
        },
    )


exception_handlers = {
    StarletteHTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
}


async def on_api_start():
    await system_router.create_tables()
    await system_router.create_admin_account()
    logger.info(f"{cfg.name}: v{cfg.version} is starting.")


async def on_api_shuttdown():
    await system_router._engine.dispose()
    logger.info(f"{cfg.name}: v{cfg.version} is shutting down.")


@event.listens_for(Engine, "first_connect")
def receive_connect(dbapi_con: DBAPIConnection, connection_record):
    "listen for the 'first_connect' event"
    logger.info(f"New Database connection: {dbapi_con.cursor().arraysize}")


@event.listens_for(Engine, "close")
def receive_close(dbapi_con: DBAPIConnection, connection_record):
    "listen for the 'close' event"
    logger.warning(f"Connection closed::{dbapi_con.cursor()} closed")


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    # logger.info("Received statement: %s", statement)
    pass


@event.listens_for(Engine, "rollback")
def receive_rollback(conn):
    "listen for the 'rollback' event"
    logger.warning("A rollback event")
