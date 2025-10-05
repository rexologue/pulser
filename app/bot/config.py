from __future__ import annotations

import os
from typing import Dict


def _read_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _load_config() -> Dict[str, str]:
    return {
        "bot_api": _read_env("TELEGRAM_API_ID", ""),
        "bot_hash": _read_env("TELEGRAM_API_HASH", ""),
        "token": _read_env("TELEGRAM_BOT_TOKEN", ""),
    }


def get_telegram_config() -> Dict[str, str]:
    return telegram_config


telegram_config = _load_config()

__all__ = ["telegram_config", "get_telegram_config"]
