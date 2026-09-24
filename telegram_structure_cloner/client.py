from __future__ import annotations

from telethon import TelegramClient

from .config import AppConfig


def create_client(config: AppConfig) -> TelegramClient:
    return TelegramClient(config.session_name, config.api_id, config.api_hash)
