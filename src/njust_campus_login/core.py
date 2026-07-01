"""Core HTTP and credential handling for the NJUST campus login CLI."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Any, Callable, Protocol

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - exercised only on minimal installs
    requests = None  # type: ignore[assignment]


DEFAULT_PORTAL_URL = "http://10.132.100.104/"
DEFAULT_LOGIN_URL = "http://10.132.100.104/api/portal/v1/login"
DEFAULT_CHECK_URL = "http://connectivitycheck.gstatic.com/generate_204"
DEFAULT_DOMAIN = "default"


class HTTPSession(Protocol):
    def get(self, url: str, **kwargs: Any) -> Any:
        ...

    def post(self, url: str, **kwargs: Any) -> Any:
        ...


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


@dataclass(frozen=True)
class LoginConfig:
    login_url: str = DEFAULT_LOGIN_URL
    portal_url: str = DEFAULT_PORTAL_URL
    domain: str = DEFAULT_DOMAIN
    timeout: float = 10.0
    warmup_portal: bool = True


@dataclass(frozen=True)
class LoginResult:
    ok: bool
    status_code: int | None
    body: str
    error: str | None = None


Emitter = Callable[[str], None]


def default_emit(message: str) -> None:
    print(message)


def normalize_url(url: str) -> str:
    return url if url.endswith("/") else f"{url}/"


def create_session() -> HTTPSession:
    if requests is None:
        raise RuntimeError("缺少 Python 依赖 requests，请先运行: python3 -m pip install -r requirements.txt")
    return requests.Session()


def parse_credentials_file(path: Path) -> Credentials:
    """Parse env-style, label-style, or two-line credential files."""
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    values: dict[str, str] = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            continue

        normalized_key = key.strip().lower().replace("-", "_")
        values[normalized_key] = value.strip().strip('"').strip("'")

    username = (
        values.get("campus_user")
        or values.get("njust_user")
        or values.get("username")
        or values.get("user")
        or values.get("account")
        or values.get("账号")
    )
    password = (
        values.get("campus_pass")
        or values.get("campus_password")
        or values.get("njust_pass")
        or values.get("njust_password")
        or values.get("password")
        or values.get("pass")
        or values.get("密码")
    )
    if username and password:
        return Credentials(username=username, password=password)

    lowered = [line.lower() for line in lines]
    for account_label in ("account", "username", "user", "账号"):
        for password_label in ("password", "pass", "密码"):
            if account_label in lowered and password_label in lowered:
                account_index = lowered.index(account_label)
                password_index = lowered.index(password_label)
                if account_index + 1 < len(lines) and password_index + 1 < len(lines):
                    return Credentials(
                        username=lines[account_index + 1],
                        password=lines[password_index + 1],
                    )

    if len(lines) >= 2:
        return Credentials(username=lines[0], password=lines[1])

    raise ValueError(f"账号密码文件格式无法识别: {path}")


def get_credentials(
    credentials_file: str | Path | None = "password.txt",
    *,
    username: str | None = None,
    password: str | None = None,
    password_stdin: bool = False,
    emit: Emitter = default_emit,
) -> Credentials:
    """Load credentials from args, env, stdin, or a local credentials file."""
    resolved_username = username or os.getenv("CAMPUS_USER") or os.getenv("NJUST_USER")
    resolved_password = password or os.getenv("CAMPUS_PASS") or os.getenv("NJUST_PASS")

    if password_stdin and not resolved_password:
        resolved_password = sys.stdin.readline().rstrip("\n")

    if resolved_username and resolved_password:
        return Credentials(username=resolved_username, password=resolved_password)

    if credentials_file:
        path = Path(credentials_file).expanduser()
        if path.exists():
            return parse_credentials_file(path)

    emit("缺少账号或密码。请设置 CAMPUS_USER/CAMPUS_PASS，或在当前目录放置 password.txt。")
    emit('示例: export CAMPUS_USER="学号"; export CAMPUS_PASS="密码"')
    raise ValueError("missing credentials")


def is_online(
    check_url: str = DEFAULT_CHECK_URL,
    *,
    timeout: float = 5.0,
    session: HTTPSession | None = None,
    emit: Emitter = default_emit,
    verbose: bool = False,
) -> bool:
    """Return True when the external connectivity check is not captive-portal redirected."""
    try:
        http = session or create_session()
        response = http.get(
            check_url,
            timeout=timeout,
            allow_redirects=False,
            headers={"User-Agent": "Mozilla/5.0"},
        )
    except RuntimeError as exc:
        emit(str(exc))
        return False
    except Exception as exc:  # requests may be unavailable in unit-test fakes
        if verbose:
            emit(f"联网检测失败，将尝试登录: {exc}")
        return False

    if verbose:
        emit(f"联网检测 HTTP 状态码: {response.status_code}")

    if check_url == DEFAULT_CHECK_URL:
        return response.status_code == 204

    return 200 <= int(response.status_code) < 300


def login(
    credentials: Credentials,
    config: LoginConfig,
    *,
    session: HTTPSession | None = None,
    emit: Emitter = default_emit,
    verbose: bool = False,
) -> LoginResult:
    """Send the same JSON payload as the NJUST portal login page."""
    try:
        http = session or create_session()
    except RuntimeError as exc:
        message = str(exc)
        emit(message)
        return LoginResult(ok=False, status_code=None, body="", error=message)

    portal_url = normalize_url(config.portal_url)

    if config.warmup_portal:
        try:
            http.get(
                portal_url,
                timeout=config.timeout,
                headers={"User-Agent": "Mozilla/5.0"},
            )
        except Exception as exc:
            if verbose:
                emit(f"登录页预访问失败，继续尝试提交登录请求: {exc}")

    payload: dict[str, Any] = {
        "domain": config.domain,
        "username": credentials.username,
        "password": credentials.password,
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Origin": portal_url.rstrip("/"),
        "Referer": portal_url,
    }

    try:
        response = http.post(
            config.login_url,
            json=payload,
            headers=headers,
            timeout=config.timeout,
        )
    except Exception as exc:
        message = f"登录请求失败: {exc}"
        emit(message)
        return LoginResult(ok=False, status_code=None, body="", error=str(exc))

    body = response.text
    emit(f"HTTP 状态码: {response.status_code}")
    emit("服务器返回:")
    emit(body)

    ok = bool(getattr(response, "ok", 200 <= int(response.status_code) < 300))
    return LoginResult(ok=ok, status_code=int(response.status_code), body=body)
