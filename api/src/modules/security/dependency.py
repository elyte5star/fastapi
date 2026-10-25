from modules.security.bearer import JWTBearer
from modules.security.ext_auth import OAuth2CodeBearer
from modules.settings.configuration import ApiConfig

cfg: ApiConfig = ApiConfig().from_toml_file().from_env_file()


security = JWTBearer()


msal_security = OAuth2CodeBearer(
    authorization_url=cfg.msal_auth_url,
    token_url=cfg.msal_token_url,
    auth_method="MSAL",
    scopes=cfg.msal_scopes,
)

google_security = OAuth2CodeBearer(
    authorization_url=cfg.google_auth_url,
    token_url=cfg.google_token_url,
    auth_method="GOOGLE",
    scopes=cfg.google_scopes,
)
