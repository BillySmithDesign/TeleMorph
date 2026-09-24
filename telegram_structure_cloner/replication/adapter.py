from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from telethon.tl.functions.channels import CreateChannelRequest, EditPhotoRequest, ToggleForumRequest
from telethon.tl.functions.messages import (
    CreateForumTopicRequest,
    EditChatAboutRequest,
    EditChatDefaultBannedRightsRequest,
)
from telethon.errors import ChatAboutNotModifiedError
from telethon.tl.types import InputChatUploadedPhoto

from .rights import build_banned_rights


class TelethonDestinationAdapter:
    def __init__(self, client: Any):
        self.client = client
        self.destination: Any | None = None

    async def create_destination(self, payload: dict[str, Any]) -> dict[str, Any]:
        target_type = payload.get("target_type")
        title = str(payload.get("title") or "Telegram Clone")
        about = str(payload.get("about") or "")
        request = CreateChannelRequest(
            title=title,
            about=about,
            broadcast=target_type == "channel",
            megagroup=target_type != "channel",
            forum=target_type == "supergroup" and bool(payload.get("forum")),
        )
        result = await self.client(request)
        self.destination = extract_created_chat(result)
        return entity_summary(self.destination)

    async def apply_destination_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        destination = self.require_destination()
        about = payload.get("about")
        if about:
            try:
                await self.client(EditChatAboutRequest(peer=destination, about=str(about)))
            except ChatAboutNotModifiedError:
                return {
                    "about_applied": False,
                    "noop": True,
                    "reason": "Destination about text was already unchanged.",
                    "unsupported_fields": unsupported_settings_fields(payload),
                }
        return {
            "about_applied": bool(about),
            "unsupported_fields": unsupported_settings_fields(payload),
            "reason": "Only destination about text is currently applied from this settings step.",
        }

    async def apply_default_permissions(self, payload: dict[str, Any]) -> dict[str, Any]:
        destination = self.require_destination()
        rights = build_banned_rights(payload.get("default_banned_rights"))
        if rights is None:
            return {"permissions_applied": False}
        await self.client(EditChatDefaultBannedRightsRequest(peer=destination, banned_rights=rights))
        return {"permissions_applied": True}

    async def configure_forum(self, payload: dict[str, Any]) -> dict[str, Any]:
        destination = self.require_destination()
        enabled = bool(payload.get("enabled"))
        tabs = bool(payload.get("tabs_enabled", False))
        await self.client(ToggleForumRequest(channel=destination, enabled=enabled, tabs=tabs))
        return {"forum_enabled": enabled, "tabs_enabled": tabs}

    async def create_forum_topic(self, payload: dict[str, Any]) -> dict[str, Any]:
        destination = self.require_destination()
        title = str(payload.get("title") or "Untitled Topic")
        request = CreateForumTopicRequest(
            peer=destination,
            title=title,
            icon_color=payload.get("icon_color"),
            icon_emoji_id=payload.get("icon_emoji_id"),
            random_id=random.getrandbits(63),
        )
        result = await self.client(request)
        return {"topic_title": title, "result_type": type(result).__name__}

    async def apply_configuration_media(self, payload: dict[str, Any]) -> dict[str, Any]:
        destination = self.require_destination()
        asset = display_photo_asset(payload)
        if asset is None:
            return {
                "unsupported": True,
                "media_applied": False,
                "reason": "No downloaded display photo asset was available.",
                "metadata_present": bool(payload),
            }
        path = Path(str(asset["path"]))
        if not path.exists():
            return {
                "failed": True,
                "failed_asset_path": str(path),
                "media_applied": False,
                "reason": "Downloaded display photo asset is missing on disk.",
            }
        uploaded = await self.client.upload_file(str(path))
        await self.client(EditPhotoRequest(channel=destination, photo=InputChatUploadedPhoto(file=uploaded)))
        return {
            "media_applied": True,
            "asset_path": str(path),
            "asset_sha256": asset.get("sha256"),
            "metadata_present": bool(payload),
        }

    def require_destination(self) -> Any:
        if self.destination is None:
            raise RuntimeError("Destination has not been created yet.")
        return self.destination


def extract_created_chat(result: Any) -> Any:
    chats = getattr(result, "chats", None)
    if chats:
        return chats[0]
    return result


def entity_summary(entity: Any) -> dict[str, Any]:
    return {
        "id": getattr(entity, "id", None),
        "title": getattr(entity, "title", None),
        "username": getattr(entity, "username", None),
        "raw_class": type(entity).__name__,
    }


def unsupported_settings_fields(payload: dict[str, Any]) -> list[str]:
    return [
        name
        for name in (
            "slowmode_seconds",
            "join_to_send",
            "join_request",
            "noforwards",
            "linked_chat_id",
            "available_reactions",
            "translations_disabled",
        )
        if payload.get(name) is not None
    ]


def display_photo_asset(payload: dict[str, Any]) -> dict[str, Any] | None:
    assets = payload.get("assets", [])
    if not isinstance(assets, list):
        return None
    for asset in assets:
        if isinstance(asset, dict) and asset.get("kind") == "display_photo" and asset.get("path"):
            return asset
    return None
