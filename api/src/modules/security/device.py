from modules.database.schema.user import DeviceMetaData
from modules.repository.queries.auth import AuthQueries
from fastapi import Request
from modules.utils.misc import get_indent, date_time_now_utc
from fastapi_events.dispatcher import dispatch
from modules.security.events.base import UserEvents, NewDeviceLogin
from modules.database.schema.user import User
import httpagentparser


class DeviceMetaDataChecker(AuthQueries):

    async def verify_device(self, user: User, request: Request):
        ip = self.get_client_ip_address(request)
        country, city = await self.get_location_from_ip(ip)
        device_details = self.get_device_details(request)
        existing_device = await self.find_existing_device(
            user.id,
            device_details,
            city,
        )
        if existing_device is None:
            new_device_meta_data = DeviceMetaData(
                id=get_indent(),
                device_details=device_details,
                location=city,
                last_login_date=date_time_now_utc(),
                userid=user.id,
            )
            await self.create_device_meta_data_query(new_device_meta_data)
            event_payload = NewDeviceLogin(
                username=user.username,
                email=user.email,
                device_details=device_details,
                ip=ip,
                location=f"{city}, {country}",
                app_url=self.get_app_url(request),
            )
            dispatch(UserEvents.UNKNOWN_DEVICE_LOGIN, event_payload)
        else:
            changes = {"last_login_date": date_time_now_utc()}
            _ = await self.update_device_meta_data_query(
                existing_device.id,
                changes,
            )

    def get_device_details(self, request: Request) -> str:
        device_details = dict(request.scope["headers"]).get(b"user-agent", b"").decode()
        if device_details is None:
            return "UNKNOWN"
        device, browser = httpagentparser.simple_detect(device_details)
        return f"Device: {device}, Browser: {browser}"

    async def find_existing_device(
        self, userid: str, device_details: str, location: str
    ) -> DeviceMetaData | None:
        known_devices = await self.find_device_meta_data_by_userid_query(userid)
        for device in known_devices:
            if device.device_details == device_details and device.location == location:
                return device
        return None

    async def login_notification(self, user: User, request: Request) -> None:
        if not self.is_geo_ip_enabled():
            self.logger.warning("GEO IP DISABALED BY ADMIN")
            return None
        await self.verify_device(user, request)
