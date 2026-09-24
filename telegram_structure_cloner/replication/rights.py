from __future__ import annotations

from datetime import datetime
from typing import Any

from telethon.tl.types import ChatBannedRights


BANNED_RIGHTS_FIELDS = {
    "view_messages",
    "send_messages",
    "send_media",
    "send_stickers",
    "send_gifs",
    "send_games",
    "send_inline",
    "embed_links",
    "send_polls",
    "change_info",
    "invite_users",
    "pin_messages",
    "manage_topics",
    "send_photos",
    "send_videos",
    "send_roundvideos",
    "send_audios",
    "send_voices",
    "send_docs",
    "send_plain",
    "edit_rank",
    "send_reactions",
    "manage_linked_peers",
}


def build_banned_rights(payload: dict[str, Any] | None) -> ChatBannedRights | None:
    if not payload:
        return None

    values = {
        key: value
        for key, value in payload.items()
        if key in BANNED_RIGHTS_FIELDS and isinstance(value, bool)
    }
    until_date = payload.get("until_date")
    parsed_until_date = parse_until_date(until_date)
    return ChatBannedRights(until_date=parsed_until_date, **values)


def parse_until_date(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
