import handler
import logging
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from starlette.staticfiles import StaticFiles
from modules.middleware.log import (
    info_file_handler,
    get_console_handler,
    smtp_log_handler,
    error_file_handler,
)
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from modules.middleware.base import (
    RateLimiterMiddleware,
)
from modules.security.events.base import APIEvents
from fastapi_events.middleware import EventHandlerASGIMiddleware
from typing import AsyncGenerator
from starlette.middleware.gzip import GZipMiddleware


# from starlette.middleware.sessions import SessionMiddleware

cfg = handler.cfg

log = handler.logger

# Set up logging
logging.basicConfig(
    handlers=[
        get_console_handler(),
        info_file_handler(),
        smtp_log_handler(cfg),
        error_file_handler(),
    ],
    encoding=cfg.encoding,
    level=cfg.log_level,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await handler.on_api_start()
    yield
    await handler.on_api_shuttdown()


app = FastAPI(
    lifespan=lifespan,
    debug=cfg.debug,
    title=cfg.name,
    description=cfg.description,
    version=cfg.version,
    terms_of_service=cfg.terms,
    contact=cfg.contacts,
    license_info=cfg.license,
    proxy_headers=True,
    forwarded_allow_ips="[::1]",
    # https://swagger.io/docs/open-source-tools/swagger-ui/usage/oauth2/
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "clientId": "",
        "clientSecret": "",
        "usePkceWithAuthorizationCodeGrant": True,
        "additionalQueryStringParams": {"prompt": "consent"},
        "appName": cfg.name,
        "scopeSeparator": " ",
    },
    swagger_ui_parameters={
        "syntaxHighlight.theme": "tomorrow-night",
        "tryItOutEnabled": True,
        "displayRequestDuration": True,
    },
    exception_handlers=handler.exception_handlers,
)

# Include routes
for route in handler.routes:
    app.include_router(route)


# Add events middleware
app.add_middleware(EventHandlerASGIMiddleware, handlers=[APIEvents(cfg)])

# Include Session
# app.add_middleware(SessionMiddleware, secret_key=cfg.secret_key, max_age=None)


ALLOWED_HOSTS = [str(origin) for origin in cfg.origins]


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# for any request that includes "gzip" in the Accept-Encoding header
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=9)

# Request limiter
app.add_middleware(RateLimiterMiddleware, config=cfg)


# Static files
app.mount("/static", StaticFiles(directory="./modules/static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return StaticFiles(directory="./modules/static")


@app.get("/", description="API root", response_class=JSONResponse)
async def root(request: Request):
    client_ip = request.client.host if request.client else ""
    log.info(f"client ip: {client_ip}")
    return JSONResponse(
        status_code=200,
        content={
            "message": "Hello Bigger Applications!",
            "success": True,
        },
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=True)
