from pathlib import Path
from os import getenv, path
from pyconfs import Configuration
import json
from pprint import pprint
from dotenv import load_dotenv
import logging
from typing import Self
from fastapi_mail import ConnectionConfig
from pydantic import SecretStr, AnyHttpUrl
from datetime import datetime

load_dotenv()


project_root = Path(__file__).parent.parent.parent
toml_path = path.join(project_root, "pyproject.toml")
email_template_path: Path = Path(__file__).parent.parent.resolve() / "templates"
config = Configuration.from_file(toml_path)


class ApiConfig:

    def __init__(self) -> None:
        # API
        self.log_level: int | str = logging.NOTSET
        self.log_file_path: str = ""
        self.host_url: str = ""
        self.debug: bool = False
        self.auth_methods: list = []
        self.origins: list[str | AnyHttpUrl] = ["http://localhost:8000"]
        self.roles: list[str] = [""]
        self.pwd_len: int = 0
        self.encoding: str = ""
        self.db_url: str = ""
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.max_login_attempt: int = 0
        self.failed_login_attempt_count: int = 0
        self.lock_duration: int = 0
        self.blocked_ips: dict[str, datetime] = {}
        self.is_geo_ip_enabled: bool = False
        self.otp_expiry: int = 0

        # PROJECT DETAILS
        self.name: str = ""
        self.version: str = ""
        self.description: str = ""
        self.terms: str = ""
        self.contacts: dict = {}
        self.license: dict = {}

        # JWT PARAMS
        self.algorithm: str = ""
        self.secret_key: str = ""
        self.rounds: int = 0
        self.token_expire_min: int = 0
        self.refresh_token_expire_min: int = 0
        self.grant_type: str = ""

        # Google AUTH
        self.google_client_id: str = ""
        self.google_client_secret: str = ""

        # MSOFT AUTH
        self.msal_tenant_id: str = ""
        self.msal_client_id: str = ""
        self.msal_client_secret: str = ""
        self.msal_scope_name: str = ""
        self.msal_scope_desc: str = "user_impersonation"
        self.msal_scopes: dict = {}
        self.msal_jwks_url: str = ""
        self.msal_auth_url: str = ""
        self.msal_token_url: str = ""
        self.msal_issuer: str = ""

        # EMAIL CONFIG
        self.email: str = ""
        self.mail_username: str = ""
        self.mail_password: str = ""
        self.mail_port: int = 0
        self.mail_server: str = ""
        self.mail_from_name: str = ""
        self.mail_starttls: bool = False
        self.mail_ssl_tls: bool = False
        self.use_credentials: bool = False
        self.validate_certs: bool = False
        self.email_config: ConnectionConfig

        # RabbitMQ
        self.rabbit_host_name: str = ""
        self.rabbit_host_port: str = ""
        self.rabbit_connect_string: str = ""
        self.rabbit_user: str = ""
        self.rabbit_pass: str = ""
        self.amqp_url: str = ""
        self.exchange_name: str = ""
        self.exchange_type: str = ""
        self.queue_names: list[str] = []

        # Visa Payment API
        self.visa_params: dict = {}

        # CLIENT
        self.client_url: str = ""

    def from_toml_file(self) -> Self:
        self.sql_username = config.database.user
        self.sql_password = config.database.pwd
        self.sql_host = config.database.host
        self.sql_port = config.database.port
        self.sql_db = config.database.db
        self.db_url = f"""postgresql+asyncpg://{self.sql_username}:
        {self.sql_password}@{self.sql_host}:{self.sql_port}/{self.sql_db}
        """
        self.log_level = getattr(logging, config.api.params["log_level"])
        self.log_file_path = config.api.params["log_file_path"]
        self.host_url = config.api.params["host_url"]
        self.debug = config.api.params["debug"]
        self.auth_methods = config.api.params["auth_methods"]
        self.max_login_attempts = config.api.params["max_login_attempts"]
        self.lock_duration = config.api.params["lock_duration"]
        self.is_geo_ip_enabled = config.api.params["enabled_geoip"]
        self.otp_expiry = config.api.params["otp_expiry"]

        self.pwd_len = config.api.params["pwd_length"]
        self.rounds = config.api.params["rounds"]
        self.encoding = config.api.params["encoding"]
        self.roles = config.api.params["roles"]

        self.rabbit_host_name = config.queue.params["host_name"]
        self.rabbit_host_port = config.queue.params["port"]
        self.rabbit_user = config.queue.params["user"]
        self.rabbit_pass = config.queue.params["pwd"]
        self.queue_names = config.queue.params["queue_names"]
        self.exchange_name = config.queue.params["exchange_name"]
        self.exchange_type = config.queue.params["exchange_type"]
        self.amqp_url = (
            f"amqp://{self.rabbit_user}:{self.rabbit_pass}@"
            + self.rabbit_host_name
            + ":"
            + self.rabbit_host_port
            + "/"
        )
        self.mail_username = config.api.contact["username"]
        self.mail_port = config.api.contact["mail_port"]
        self.mail_server = config.api.contact["mail_server"]
        self.mail_from_name = config.api.contact["mail_from_name"]
        self.mail_starttls = config.api.contact["mail_starttls"]
        self.mail_ssl_tls = config.api.contact["mail_ssl_tls"]
        self.email = config.api.contact["email"]

        self.name = config.api.doc["name"]
        self.terms = config.api.doc["terms_of_service"]
        self.version = config.tool.poetry["version"]
        self.description = config.api.doc["description"]
        self.contacts = config.api.contact.as_dict()
        self.license = config.api.license.as_dict()

        self.algorithm = config.api.params["algorithm"]
        self.secret_key = config.api.params["secret_key"]
        self.token_expire_min = config.api.params["token_expire_min"]
        self.refresh_token_expire_min = config.api.params["refresh_token_expire_min"]

        # Visa Payment API
        self.visa_params = config.visa.params.as_dict()
        return self

    def from_env_file(self) -> Self:
        self.db_url = str(getenv("DB_URL"))
        self.amqp_url = str(getenv("RQ_URL"))
        self.token_expire_min = int(getenv("JWT_EXPIRE_MINUTES", self.token_expire_min))
        self.mail_password = str(getenv("MAIL_PASSWORD"))
        self.email_config = ConnectionConfig(
            MAIL_USERNAME=self.mail_username,
            MAIL_PASSWORD=SecretStr(self.mail_password),
            MAIL_FROM=self.email,
            MAIL_PORT=self.mail_port,
            MAIL_SERVER=self.mail_server,
            MAIL_STARTTLS=self.mail_starttls,
            MAIL_SSL_TLS=self.mail_ssl_tls,
            MAIL_DEBUG=0,
            MAIL_FROM_NAME=self.mail_from_name,
            TEMPLATE_FOLDER=email_template_path,
        )
        if self.log_file_path == "":
            self.log_file_path = str(getenv("LOG_PATH"))
        self.origins = json.loads(getenv("CORS_ORIGINS", '["*"]'))
        self.client_url = str(getenv("CLIENT_URL", self.client_url))
        self.log_level = getenv("LOG_LEVEL", self.log_level)
        self.refresh_token_expire_min = int(
            getenv(
                "JWT_REFRESH_TOKEN_EXPIRE_MINUTES",
                self.refresh_token_expire_min,
            )
        )
        self.msal_tenant_id = str(getenv("MICROSOFT_TENANT_ID"))
        self.msal_client_id = str(getenv("MICROSOFT_CLIENT_ID"))
        self.msal_client_secret = str(getenv("MICROSOFT_CLIENT_SECRET"))
        self.msal_scope_desc = str(getenv("MICROSOFT_SCOPE_DESC", self.msal_scope_desc))
        self.msal_scope_name = f"api://{self.msal_client_id}/{self.msal_scope_desc}"
        self.msal_scopes = {self.msal_scope_name: self.msal_scope_desc}
        self.msal_jwks_url = f"https://login.microsoftonline.com/{self.msal_tenant_id}/discovery/v2.0/keys"
        self.msal_auth_url = f"https://login.microsoftonline.com/{self.msal_tenant_id}/oauth2/v2.0/authorize"
        self.msal_token_url = (
            f"https://login.microsoftonline.com/{self.msal_tenant_id}/oauth2/v2.0/token"
        )
        self.msal_issuer = (
            f"https://login.microsoftonline.com/{self.msal_tenant_id}/v2.0"
        )

        self.google_client_id = str(getenv("GOOGLE_CLIENT_ID"))
        self.google_scope_name = "https://www.googleapis.com/auth/userinfo.email"
        self.google_client_secret = str(getenv("GOOGLE_CLIENT_SECRET"))
        self.google_audience = f"{self.google_client_id}.apps.googleusercontent.com"
        self.google_issuer = "https://accounts.google.com"
        self.google_auth_url = "https://accounts.google.com/o/oauth2/auth"
        self.google_token_url = "https://oauth2.googleapis.com/token"
        self.google_token_info_url = "https://www.googleapis.com/oauth2/v3/tokeninfo"
        self.google_scopes = {"https://www.googleapis.com/auth/userinfo.email": ""}

        return self

    def pretty_print(self):
        pprint(vars(self))
