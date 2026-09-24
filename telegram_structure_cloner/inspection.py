from __future__ import annotations

from typing import Any

from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetForumTopicsRequest, GetFullChatRequest
from telethon.tl.types import Channel, Chat

from .blueprint import Blueprint
from .media_assets import DEFAULT_ASSET_DIR, download_config_photo
from .serialization import public_attrs, sanitize


async def inspect_source(client: Any, entity: Any, asset_dir: str = DEFAULT_ASSET_DIR) -> Blueprint:
    blueprint = Blueprint.empty()
    blueprint.source = extract_identity(entity)
    full = await fetch_full_entity(client, entity, blueprint)
    blueprint.settings = extract_settings(entity, full, blueprint)
    blueprint.permissions = extract_permissions(entity, full, blueprint)
    blueprint.configuration_media = extract_configuration_media(entity, full, blueprint)
    await attach_configuration_assets(client, entity, blueprint, asset_dir)
    blueprint.forum = await extract_forum(client, entity, full, blueprint)
    record_known_gaps(entity, blueprint)
    return blueprint


async def attach_configuration_assets(
    client: Any,
    entity: Any,
    blueprint: Blueprint,
    asset_dir: str,
) -> None:
    if not blueprint.configuration_media.get("photo") and not blueprint.configuration_media.get("chat_photo"):
        return
    try:
        asset = await download_config_photo(client, entity, asset_dir=asset_dir)
    except Exception as exc:
        blueprint.add_unsupported(
            "configuration_media.display_photo_asset",
            f"Display photo could not be downloaded: {type(exc).__name__}: {exc}",
            severity="warning",
        )
        return
    if asset is None:
        blueprint.add_unsupported(
            "configuration_media.display_photo_asset",
            "Telegram did not return a downloadable display photo asset.",
            severity="warning",
        )
        return
    blueprint.configuration_media.setdefault("assets", []).append(asset)


def extract_identity(entity: Any) -> dict[str, Any]:
    return {
        "id": sanitize(getattr(entity, "id", None)),
        "access_hash": sanitize(getattr(entity, "access_hash", None)),
        "title": sanitize(getattr(entity, "title", None)),
        "username": sanitize(getattr(entity, "username", None)),
        "usernames": sanitize(getattr(entity, "usernames", None)),
        "type": classify_entity(entity),
        "raw_class": type(entity).__name__,
        "is_broadcast": bool(getattr(entity, "broadcast", False)),
        "is_megagroup": bool(getattr(entity, "megagroup", False)),
        "is_forum": bool(getattr(entity, "forum", False)),
        "date": sanitize(getattr(entity, "date", None)),
    }


def classify_entity(entity: Any) -> str:
    if isinstance(entity, Channel):
        if getattr(entity, "broadcast", False):
            return "channel"
        if getattr(entity, "megagroup", False):
            return "supergroup_forum" if getattr(entity, "forum", False) else "supergroup"
        return "channel_like"
    if isinstance(entity, Chat):
        return "group"
    return type(entity).__name__.lower()


async def fetch_full_entity(client: Any, entity: Any, blueprint: Blueprint) -> Any | None:
    try:
        if isinstance(entity, Channel):
            return await client(GetFullChannelRequest(entity))
        if isinstance(entity, Chat):
            return await client(GetFullChatRequest(entity.id))
    except Exception as exc:
        blueprint.add_unsupported(
            "settings.full_entity",
            f"Telegram did not return full entity details: {type(exc).__name__}: {exc}",
            severity="warning",
        )
    return None


def extract_settings(entity: Any, full: Any, blueprint: Blueprint) -> dict[str, Any]:
    full_chat = getattr(full, "full_chat", None)
    settings = {
        "entity_flags": {
            "creator": sanitize(getattr(entity, "creator", None)),
            "left": sanitize(getattr(entity, "left", None)),
            "verified": sanitize(getattr(entity, "verified", None)),
            "restricted": sanitize(getattr(entity, "restricted", None)),
            "signatures": sanitize(getattr(entity, "signatures", None)),
            "noforwards": sanitize(getattr(entity, "noforwards", None)),
            "join_to_send": sanitize(getattr(entity, "join_to_send", None)),
            "join_request": sanitize(getattr(entity, "join_request", None)),
        },
        "about": sanitize(getattr(full_chat, "about", None)),
        "participants_count": sanitize(getattr(full_chat, "participants_count", None)),
        "admins_count": sanitize(getattr(full_chat, "admins_count", None)),
        "kicked_count": sanitize(getattr(full_chat, "kicked_count", None)),
        "banned_count": sanitize(getattr(full_chat, "banned_count", None)),
        "linked_chat_id": sanitize(getattr(full_chat, "linked_chat_id", None)),
        "slowmode_seconds": sanitize(getattr(full_chat, "slowmode_seconds", None)),
        "available_min_id": sanitize(getattr(full_chat, "available_min_id", None)),
        "reactions": sanitize(getattr(full_chat, "available_reactions", None)),
        "raw_entity": public_attrs(entity),
        "raw_full_chat": public_attrs(full_chat),
    }
    if full_chat is None:
        blueprint.add_unsupported(
            "settings.full_chat",
            "Full chat settings were not available for this source/account.",
            severity="warning",
        )
    return settings


def extract_permissions(entity: Any, full: Any, blueprint: Blueprint) -> dict[str, Any]:
    full_chat = getattr(full, "full_chat", None)
    permissions = {
        "default_banned_rights": sanitize(getattr(entity, "default_banned_rights", None)),
        "admin_rights": sanitize(getattr(entity, "admin_rights", None)),
        "banned_rights": sanitize(getattr(entity, "banned_rights", None)),
        "full_chat_default_banned_rights": sanitize(
            getattr(full_chat, "default_banned_rights", None)
        ),
    }
    if permissions["default_banned_rights"] is None:
        blueprint.add_unsupported(
            "permissions.default_banned_rights",
            "Default permissions are absent or not exposed for this entity type.",
        )
    return permissions


def extract_configuration_media(entity: Any, full: Any, blueprint: Blueprint) -> dict[str, Any]:
    full_chat = getattr(full, "full_chat", None)
    media = {
        "photo": sanitize(getattr(entity, "photo", None)),
        "chat_photo": sanitize(getattr(full_chat, "chat_photo", None)),
        "profile_photo": sanitize(getattr(full_chat, "profile_photo", None)),
        "theme_emoticon": sanitize(getattr(full_chat, "theme_emoticon", None)),
        "emoji_status": sanitize(getattr(entity, "emoji_status", None)),
    }
    if media["photo"] is None and media["chat_photo"] is None:
        blueprint.add_unsupported(
            "configuration_media.photo",
            "No configuration media metadata was available.",
        )
    return media


async def extract_forum(client: Any, entity: Any, full: Any, blueprint: Blueprint) -> dict[str, Any]:
    enabled = bool(getattr(entity, "forum", False))
    forum = {
        "enabled": enabled,
        "tabs_enabled": sanitize(getattr(getattr(full, "full_chat", None), "forum_tabs", None)),
        "topics": [],
    }
    if not enabled:
        return forum

    try:
        result = await client(
            GetForumTopicsRequest(
                peer=entity,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100,
            )
        )
    except Exception as exc:
        blueprint.add_unsupported(
            "forum.topics",
            f"Forum topics could not be listed: {type(exc).__name__}: {exc}",
            severity="warning",
        )
        return forum

    topics = getattr(result, "topics", []) or []
    forum["topics"] = [sanitize(topic) for topic in topics]
    if getattr(result, "count", None) and len(topics) < result.count:
        blueprint.add_unsupported(
            "forum.topics.pagination",
            "More than 100 topics exist; M1 exported the first page only.",
            severity="warning",
        )
    return forum


def record_known_gaps(entity: Any, blueprint: Blueprint) -> None:
    blueprint.add_unsupported(
        "members",
        "Member export is intentionally out of scope for M1 and was not requested.",
    )
    blueprint.add_unsupported(
        "messages",
        "Message export is intentionally out of scope for M1 and was not requested.",
    )
    blueprint.add_unsupported(
        "invite_links",
        "Existing invite links require additional privileged API calls and are not exported in M1.",
    )
    if not isinstance(entity, Channel | Chat):
        blueprint.add_unsupported(
            "source.entity_type",
            "This entity type is not a channel, group, supergroup, or forum.",
            severity="warning",
        )
