from modules.security.device import DeviceMetaDataChecker
from fastapi import Request
from modules.database.schema.user import NewLocationToken, UserLocation, User
from modules.utils.misc import get_indent
from fastapi_events.dispatcher import dispatch
from modules.security.events.base import UserEvents, StrangeLocation


class DifferentLocationChecker(DeviceMetaDataChecker):

    async def check_strange_location(
        self,
        user: User,
        request: Request,
    ) -> bool:
        ip_address = self.get_client_ip_address(request)
        loc_token = await self.is_new_login_location(user, ip_address)
        if loc_token is not None:
            app_url = self.get_app_url(request)
            event_payload = StrangeLocation(
                app_url=app_url,
                ip=ip_address,
                token=loc_token.token,
                username=user.username,
                email=user.email,
                country=loc_token.location.country,
            )
            dispatch(UserEvents.STRANGE_LOCATION, event_payload)
            return True
        return False

    async def is_new_login_location(
        self,
        user: User,
        ip: str,
    ) -> NewLocationToken | None:
        if not self.is_geo_ip_enabled():
            self.logger.warning("GEO IP DISABALED BY ADMIN")
            return None
        country, city = await self.get_location_from_ip(ip)
        self.logger.debug(f"country: {country}, city: {city}")
        user_loc = await self.find_user_location_by_country_and_user_query(
            country, user
        )
        if user_loc is None:
            return await self.create_new_location_token(user, country)
        elif not user_loc.enabled:
            await self.del_user_location_query(user_loc.id)
            return await self.create_new_location_token(user, country)
        return None

    async def create_new_location_token(
        self, user: User, country: str
    ) -> NewLocationToken | None:
        user_loc = UserLocation(id=get_indent(), country=country, owner=user)
        user_loc = await self.create_user_location_query(user_loc)
        token = self.create_timed_token(user.email)
        new_loc_token = NewLocationToken(
            id=get_indent(), token=token, location=user_loc
        )
        new_loc_token = await self.create_new_location_token_query(
            new_loc_token,
        )
        return new_loc_token
