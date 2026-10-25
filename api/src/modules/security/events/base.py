from enum import Enum
from fastapi_events.typing import Event
from fastapi_events.handlers.base import BaseEventHandler
from modules.security.events.email import EmailService
from modules.settings.configuration import ApiConfig
from pydantic import BaseModel, EmailStr
from fastapi_events.registry.payload_schema import registry as payload_schema
from datetime import datetime
from modules.repository.request_models.user import EmailRequestSchema
from modules.utils.misc import date_time_now_utc_tz
from pydantic import AnyHttpUrl

class UserEvents(Enum):
    SIGNED_UP = "USER_SIGNED_UP"
    ACTIVATED = "USER_ACTIVATED"
    RESET_PASSWORD = "USER_PASSWORD"
    CLIENT_ENQUIRY = "INQUIRY"
    OTP = "USER_OTP"
    STRANGE_LOCATION = "USER_LOCATION"
    BLOCKED = "USER_BLOCKED"
    BOOKING = "USER_BOOKING"
    USER_AUTH_SUCCESS = "USER_AUTH_SUCCESS"
    USER_AUTH_FAILURE = "USER_AUTH_FAILURE"
    UNKNOWN_USER_AUTH_FAILURE = "BRUTE_FORCE"
    UNKNOWN_DEVICE_LOGIN = "NEW_DEVICE_LOGIN"
    UPDATED_USER_PASSWORD = "UPDATED_USER_PASSWORD"


@payload_schema.register(event_name=UserEvents.SIGNED_UP)
class SignUpPayload(BaseModel):
    userid: str
    username: str
    email: EmailStr
    expiry: datetime
    token: str
    app_url: str | AnyHttpUrl
    # locale:str future?


@payload_schema.register(event_name=UserEvents.UPDATED_USER_PASSWORD)
class UserPasswordChange(BaseModel):
    username: str
    email: str
    modified_by: str


@payload_schema.register(event_name=UserEvents.STRANGE_LOCATION)
class StrangeLocation(BaseModel):
    username: str
    ip: str
    token: str
    app_url: str
    email: EmailStr
    country: str
    # locale:str future?


@payload_schema.register(event_name=UserEvents.UNKNOWN_DEVICE_LOGIN)
class NewDeviceLogin(BaseModel):
    username: str
    email: EmailStr
    device_details: str
    ip: str
    location: str
    app_url: str | AnyHttpUrl
    # locale:str future?


@payload_schema.register(event_name=UserEvents.CLIENT_ENQUIRY)
class ClientEnquiry(BaseModel):
    eid: str
    client_name: str
    email: EmailStr
    message: str
    app_url: str | AnyHttpUrl
    expiry: datetime

@payload_schema.register(event_name=UserEvents.BLOCKED)
class BlockedUserAccount(BaseModel):
    userid: str
    username: str
    email: EmailStr
    blocked_date: datetime


@payload_schema.register(event_name=UserEvents.RESET_PASSWORD)
class ResetUserPassword(BaseModel):
    username: str
    email: EmailStr
    app_url: str | AnyHttpUrl
    token: str
    expiry: datetime


class APIEventsHandler(EmailService):

    async def unknown_device_notification(self, event_payload: NewDeviceLogin):
        subject = "New device login notification"
        body = {
            "device_details": event_payload.device_details,
            "location": event_payload.location,
            "ip": event_payload.ip,
            "home": event_payload.app_url,
            "username": event_payload.username
        }
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=[event_payload.email],
            body=body,
            template_name="new_device.html",
        )
        is_sent = await self.send_email_to_user(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{event_payload.email}")
            return True
        self.config.logger.warning(f"Email not sent to :{event_payload.email}")
        return False

    async def confirm_registration(
        self,
        event_payload: SignUpPayload,
    ):
        subject = "Registration confirmation"
        expiry = event_payload.expiry
        body = {
            "confirmationUrl": f"{event_payload.app_url}/user/signup/verify-otp?token={event_payload.token}",
            "otp": event_payload.token,
            "username": event_payload.username,
            "message": event_payload.userid,
            "expiry": f" The OTP link expires on {expiry.strftime("%d/%m/%Y, %H:%M")}.",
            "home": event_payload.app_url,
        }
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=[event_payload.email],
            body=body,
            template_name="confirm_registration.html",
        )
        is_sent = await self.send_email_to_user(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{event_payload.email}")
            return True
        self.config.logger.warning(f"Email not sent to :{event_payload.email}")
        return False

    async def strange_location_login(self, event_payload: StrangeLocation):
        subject = "Login attempt from a different location"
        body = {
            "country": event_payload.country,
            "username": event_payload.username,
            "ip": event_payload.ip,
            "time": date_time_now_utc_tz().strftime("%d-%m-%Y, %H:%M:%S"),
            "enableLocationLink": f"{event_payload.app_url}/auth/enable-new-location?token={event_payload.token}",
            "changePassUri": event_payload.app_url + "/user/update-password",

        }
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=[str(event_payload.email)],
            body=body,
            template_name="unusual_location.html",
        )
        is_sent = await self.send_email_to_user(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{event_payload.email}")
            return True
        self.config.logger.warning(f"Email not sent to :{event_payload.email}")
        return False

    async def client_enquiry(self, event_payload: ClientEnquiry):
        subject = "New client enquiry"
        body = {
            "message": event_payload.message,
            "case_id": event_payload.eid,
            "client_name": event_payload.client_name,
            "time": date_time_now_utc_tz().strftime('%d-%m-%Y, %H:%M:%S'),
            "home": event_payload.app_url,
        }
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=[str(event_payload.email), self.config.email],
            body=body,
            template_name="enquiry.html",
        )
        is_sent = await self.send_email_to_user(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{email_req.recipients}")
            return True
        return False

    async def reset_user_password(self, event_payload: ResetUserPassword):
        subject = "Reset password"
        expiry = event_payload.expiry
        body = {
            "home": event_payload.app_url,
            "username": event_payload.username,
            "resetLink": f"{event_payload.app_url}/user/change-password?token={event_payload.token}",
            "expiry": expiry.strftime("%d/%m/%Y,%H:%M"),
            "token": event_payload.token,
        }
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=[event_payload.email],
            body=body,
            template_name="reset_password.html",
        )
        is_sent = await self.send_email_to_user(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{email_req.recipients}")
            return True
        return False

    async def password_change(self, event_payload: UserPasswordChange):
        html = f"""<p>Hey {event_payload.username},
            your password was changed by: {event_payload.modified_by}.
            If this wasn't you, go to our site and reset your password.</p> """
        subject = "Your password was changed"
        email_req = EmailRequestSchema(
            subject=subject,
            recipients=[event_payload.email],
            body={"message": html},
        )
        is_sent = await self.send_without_template(email_req)
        if is_sent:
            self.config.logger.info(f"Email sent to :{email_req.recipients}")
            return True
        return False


class APIEvents(BaseEventHandler):
    def __init__(self, cfg: ApiConfig):
        self.event_handler = APIEventsHandler(cfg)
        self.cfg = cfg

    async def handle(self, event: Event) -> None:
        event_name, payload = event
        match event_name:
            case UserEvents.SIGNED_UP:
                await self.event_handler.confirm_registration(payload)
            case UserEvents.STRANGE_LOCATION:
                await self.event_handler.strange_location_login(payload)
            case UserEvents.UNKNOWN_DEVICE_LOGIN:
                await self.event_handler.unknown_device_notification(payload)
            case UserEvents.CLIENT_ENQUIRY:
                await self.event_handler.client_enquiry(payload)
            case UserEvents.RESET_PASSWORD:
                await self.event_handler.reset_user_password(payload)
            case UserEvents.UPDATED_USER_PASSWORD:
                await self.event_handler.password_change(payload)
            case _:
                self.cfg.logger.warning(payload)
