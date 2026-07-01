"""NJUST campus network login helper."""

from .core import (
    DEFAULT_CHECK_URL,
    DEFAULT_DOMAIN,
    DEFAULT_LOGIN_URL,
    DEFAULT_PORTAL_URL,
    Credentials,
    LoginConfig,
    LoginResult,
    get_credentials,
    is_online,
    login,
    parse_credentials_file,
)

__all__ = [
    "DEFAULT_CHECK_URL",
    "DEFAULT_DOMAIN",
    "DEFAULT_LOGIN_URL",
    "DEFAULT_PORTAL_URL",
    "Credentials",
    "LoginConfig",
    "LoginResult",
    "get_credentials",
    "is_online",
    "login",
    "parse_credentials_file",
]
