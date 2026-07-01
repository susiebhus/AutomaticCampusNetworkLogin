"""Command-line interface for NJUST campus network login."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time
from typing import Callable

from .core import (
    DEFAULT_CHECK_URL,
    DEFAULT_DOMAIN,
    DEFAULT_LOGIN_URL,
    DEFAULT_PORTAL_URL,
    LoginConfig,
    get_credentials,
    is_online,
    login,
)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="njust-campus-login",
        description="从命令行登录南京理工大学校园网认证系统，无需打开浏览器。",
    )
    parser.add_argument(
        "--login-url",
        default=os.getenv("CAMPUS_LOGIN_URL", DEFAULT_LOGIN_URL),
        help=f"登录接口，默认 {DEFAULT_LOGIN_URL}",
    )
    parser.add_argument(
        "--portal-url",
        default=os.getenv("CAMPUS_PORTAL_URL", DEFAULT_PORTAL_URL),
        help=f"认证页面地址，默认 {DEFAULT_PORTAL_URL}",
    )
    parser.add_argument(
        "--domain",
        default=os.getenv("CAMPUS_DOMAIN", DEFAULT_DOMAIN),
        help=f"服务域，默认 {DEFAULT_DOMAIN}",
    )
    parser.add_argument(
        "--timeout",
        type=non_negative_float,
        default=env_float("CAMPUS_TIMEOUT", 10.0),
        help="HTTP 超时时间，默认 10 秒",
    )
    parser.add_argument(
        "--retries",
        type=positive_int,
        default=env_int("CAMPUS_RETRIES", 1),
        help="登录重试次数，默认 1",
    )
    parser.add_argument(
        "--retry-delay",
        type=non_negative_float,
        default=env_float("CAMPUS_RETRY_DELAY", 5.0),
        help="重试间隔，默认 5 秒",
    )
    parser.add_argument(
        "--check-url",
        default=os.getenv("CAMPUS_CHECK_URL", DEFAULT_CHECK_URL),
        help=f"联网检测 URL，默认 {DEFAULT_CHECK_URL}",
    )
    parser.add_argument("--check", action="store_true", help="只检测当前是否已连通外网，不执行登录")
    parser.add_argument("--skip-if-online", action="store_true", help="已联网时跳过登录")
    parser.add_argument("--verify-after-login", action="store_true", help="登录成功后再次检测外网连通性")
    parser.add_argument("--no-warmup", action="store_true", help="登录前不预访问认证页")
    parser.add_argument(
        "--credentials-file",
        default=os.getenv("CAMPUS_CREDENTIALS_FILE", "password.txt"),
        help="账号密码文件路径，默认 ./password.txt",
    )
    parser.add_argument("--user", help="用户名；也可使用 CAMPUS_USER 或 NJUST_USER")
    parser.add_argument("--password-stdin", action="store_true", help="从标准输入读取一行密码")
    parser.add_argument("--log-file", help="同时把输出追加写入日志文件")
    parser.add_argument("--verbose", action="store_true", help="输出更多诊断信息")
    return parser


def build_emitter(log_file: str | None) -> Callable[[str], None]:
    log_path = Path(log_file).expanduser() if log_file else None

    def emit(message: str) -> None:
        print(message)
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"{message}\n")

    return emit


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    emit = build_emitter(args.log_file)

    if args.check:
        if is_online(args.check_url, timeout=args.timeout, emit=emit, verbose=args.verbose):
            emit("当前已联网。")
            return 0
        emit("当前未检测到外网连通。")
        return 1

    if args.skip_if_online and is_online(args.check_url, timeout=args.timeout, emit=emit, verbose=args.verbose):
        emit("当前已联网，跳过校园网登录。")
        return 0

    try:
        credentials = get_credentials(
            args.credentials_file,
            username=args.user,
            password_stdin=args.password_stdin,
            emit=emit,
        )
    except ValueError:
        return 2

    config = LoginConfig(
        login_url=args.login_url,
        portal_url=args.portal_url,
        domain=args.domain,
        timeout=args.timeout,
        warmup_portal=not args.no_warmup,
    )

    for attempt in range(1, args.retries + 1):
        if args.retries > 1:
            emit(f"登录尝试 {attempt}/{args.retries}")

        result = login(credentials, config, emit=emit, verbose=args.verbose)
        if result.ok:
            if args.verify_after_login:
                time.sleep(2)
                if is_online(args.check_url, timeout=args.timeout, emit=emit, verbose=args.verbose):
                    emit("登录后外网连通性检测通过。")
                    return 0
                emit("登录请求已返回成功，但外网连通性检测未通过。")
                return 1
            return 0

        if attempt < args.retries:
            time.sleep(args.retry_delay)

    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
