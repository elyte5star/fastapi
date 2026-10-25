from starlette.requests import Request
from fastapi import status
from modules.settings.configuration import ApiConfig
from starlette.types import ASGIApp, Message, Scope, Receive, Send
from starlette.responses import JSONResponse, RedirectResponse
from starlette.datastructures import URL, MutableHeaders
from modules.utils.misc import (
    TokenBucket,
    get_client_ip_address,
    time_delta,
    date_time_now_utc_tz,
)


# Request limiter algorithm


# redirections = {
#     "/v1/resource/": "/v2/resource/",
#     # ...
# }


class RedirectsMiddleware:
    def __init__(self, app, path_mapping: dict):
        self.app = app
        self.path_mapping = path_mapping

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        url = URL(scope=scope)

        if url.path in self.path_mapping:
            url = url.replace(path=self.path_mapping[url.path])
            response = RedirectResponse(url, status_code=301)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


class RateLimiterMiddleware:
    def __init__(self, app: ASGIApp, config: ApiConfig) -> None:
        self.app = app
        self.bucket = TokenBucket(3, 2)  # 3 request per 2 second
        self.cf = config

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        request = Request(scope, receive)

        if not self.bucket.check():
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Path": request.url.path, "Method": request.method},
                content={
                    "message": "Too many Requests",
                    "success": False,
                },
            )
            self.cf.logger.warning("Request packet dropped")
            return await response(scope, receive, send)

        ip = get_client_ip_address(request)
        # ip unblocked ip after 1hr
        refresh_time_delta = date_time_now_utc_tz() - time_delta(minutes=60)

        if ip in self.cf.blocked_ips:
            lock_time = self.cf.blocked_ips[ip]
            if lock_time < refresh_time_delta:
                removed_ip = self.cf.blocked_ips.pop(ip)
                self.cf.logger.warning(
                    f"Ip: {removed_ip} removed from blacklist ",
                )
            else:
                wait_duration = lock_time - refresh_time_delta
                seconds = wait_duration.total_seconds()
                hrs, mins, _ = (
                    int(seconds // 3600),
                    int(seconds % 3600) // 60,
                    seconds % 60,
                )
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "message": f"""Too many failed attempts,
                                Retry after {hrs} hours, {mins} minutes""",
                        "success": False,
                    },
                    headers={
                        "Retry-After": f"{hrs} hours, {mins} minutes",
                        "Path": request.url.path,
                        "Method": request.method,
                    },
                )
                return await response(scope, receive, send)

        body_size = 0
        http_status_code: int | None = None

        async def receive_logging_request_body_size():
            nonlocal body_size
            message = await receive()
            assert message["type"] == "http.request"
            body_size += len(message.get("body", b""))
            if not message.get("more_body", False):
                self.cf.logger.debug(f"Size of request body was: {body_size} bytes")
            return message

        async def send_with_extra_headers(message: Message) -> None:
            nonlocal http_status_code
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                http_status_code = message["status"]
                headers["path"] = request.url.path
                headers["httpStatus"] = f"{http_status_code}"
                headers["method"] = f"{request.method}"

            await send(message)

        await self.app(
            scope, receive_logging_request_body_size, send_with_extra_headers
        )
