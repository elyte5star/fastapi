from modules.database.schema.user import User
from fastapi import Request
from modules.settings.configuration import ApiConfig
from modules.security.location import DifferentLocationChecker
from modules.utils.misc import date_time_now_utc_tz


class LoginAttemptChecker(DifferentLocationChecker):
    def __init__(self, config: ApiConfig):
        super().__init__(config)
        self.active_user_store: list = []

    def get_cookies(self, name: str, request: Request) -> str | None:
        cookie = request.cookies.get(name)
        if cookie is not None:
            return cookie
        self.logger.warning(f"Cookie with name :{name} not found!")
        return None

    async def reset_failed_attempts(self, user: User) -> None:
        if user.failed_attempts > 0:
            await self.update_user_info(user.id, dict(failed_attempts=0))
        self.cf.failed_login_attempt_count = 0

    async def increase_user_failed_attempts(self, user: User) -> None:
        user_failed_attempts = user.failed_attempts
        if user_failed_attempts >= self.cf.max_login_attempt:
            await self.lock_user_account_query(user)
        else:
            userid = user.id
            changes = dict(failed_attempts=user_failed_attempts + 1)
            await self.update_user_info(userid, changes)

    async def increase_unknown_user_failed_attempts(self, request: Request) -> None:
        ip_address = self.get_client_ip_address(request)
        if self.cf.failed_login_attempt_count >= self.cf.max_login_attempt:
            self.cf.blocked_ips[ip_address] = date_time_now_utc_tz()
            self.cf.failed_login_attempt_count = 0
            self.cf.logger.warning(
                f"Potential brute-force attack, ip address {ip_address} added to black list"
            )
        else:
            self.cf.failed_login_attempt_count += 1
