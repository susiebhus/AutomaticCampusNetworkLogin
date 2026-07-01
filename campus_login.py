#!/usr/bin/env python3
"""Compatibility wrapper for running the campus login CLI directly."""

from pathlib import Path
import sys


SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from njust_campus_login.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
