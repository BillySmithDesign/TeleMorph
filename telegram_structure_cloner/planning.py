from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .blueprint import SCHEMA_VERSION
from .validation import ValidationResult, validate_blueprint


PLAN_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class PlanStep:
    id: str
    action: str
    status: str
    reason: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DestinationPlan:
    plan_schema_version: str
    blueprint_schema_version: str | None
    generated_at: str
    dry_run: bool
    destination_title: str
    validation: dict[str, Any]
    steps: list[PlanStep]
    warnings: list[str]
    blocked_properties: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["steps"] = [asdict(step) for step in self.steps]
        return data


def build_destination_plan(
    blueprint: dict[str, Any],
    destination_title: str | None = None,
) -> DestinationPlan:
    validation = validate_blueprint(blueprint)
    source = blueprint.get("source", {}) if isinstance(blueprint.get("source"), dict) else {}
    planned_title = destination_title or default_destination_title(source)
    steps: list[PlanStep] = []
    warnings: list[str] = []

    add_identity_step(steps, source, blueprint, planned_title)
    add_settings_step(steps, blueprint, warnings)
    add_permissions_step(steps, blueprint, warnings)
    add_forum_steps(steps, blueprint, warnings)
    add_media_step(steps, blueprint, warnings)

    if not validation.valid:
        warnings.append("Plan contains blocked steps because blueprint validation failed.")
        steps = [
            PlanStep(
                id=step.id,
                action=step.action,
                status="blocked",
                reason="Blueprint validation must pass before this step can be executed.",
                payload=step.payload,
            )
            for step in steps
        ]

    return DestinationPlan(
        plan_schema_version=PLAN_SCHEMA_VERSION,
        blueprint_schema_version=blueprint.get("schema_version"),
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        dry_run=True,
        destination_title=planned_title,
        validation=validation.to_dict(),
        steps=steps,
        warnings=warnings,
        blocked_properties=collect_blocked_properties(blueprint, validation),
    )


def default_destination_title(source: dict[str, Any]) -> str:
    title = source.get("title") or "Telegram Clone"
    return f"{title} Clone"


def add_identity_step(
    steps: list[PlanStep],
    source: dict[str, Any],
    blueprint: dict[str, Any],
    destination_title: str,
) -> None:
    source_type = source.get("type", "unknown")
    settings = blueprint.get("settings", {})
    forum = blueprint.get("forum", {})
    action = "create_destination"
    if source_type == "channel":
        target_type = "channel"
    elif source_type in {"group", "supergroup", "supergroup_forum"}:
        target_type = "supergroup"
    else:
        target_type = "chat"

    steps.append(
        PlanStep(
            id="create_destination",
            action=action,
            status="planned",
            reason="Create the destination container without copying messages or members.",
            payload={
                "source_type": source_type,
                "target_type": target_type,
                "title": destination_title,
                "about": settings.get("about") if isinstance(settings, dict) else "",
                "forum": bool(forum.get("enabled")) if isinstance(forum, dict) else False,
                "copy_username": False,
                "copy_members": False,
                "copy_messages": False,
            },
        )
    )


def add_settings_step(
    steps: list[PlanStep],
    blueprint: dict[str, Any],
    warnings: list[str],
) -> None:
    settings = blueprint.get("settings", {})
    raw_full_chat = settings.get("raw_full_chat", {}) if isinstance(settings, dict) else {}
    payload = {
        "about": settings.get("about") if isinstance(settings, dict) else None,
        "slowmode_seconds": settings.get("slowmode_seconds") if isinstance(settings, dict) else None,
        "join_to_send": nested_get(blueprint, "settings.entity_flags.join_to_send"),
        "join_request": nested_get(blueprint, "settings.entity_flags.join_request"),
        "noforwards": nested_get(blueprint, "settings.entity_flags.noforwards"),
        "linked_chat_id": settings.get("linked_chat_id") if isinstance(settings, dict) else None,
        "available_reactions": settings.get("reactions") if isinstance(settings, dict) else None,
    }
    if raw_full_chat.get("translations_disabled") is not None:
        payload["translations_disabled"] = raw_full_chat["translations_disabled"]

    warnings.append("Some settings may require admin privileges or may be unavailable on destination.")
    steps.append(
        PlanStep(
            id="apply_settings",
            action="apply_destination_settings",
            status="planned",
            reason="Apply Telegram settings that have destination-side equivalents.",
            payload=payload,
        )
    )


def add_permissions_step(
    steps: list[PlanStep],
    blueprint: dict[str, Any],
    warnings: list[str],
) -> None:
    permissions = blueprint.get("permissions", {})
    default_rights = (
        permissions.get("default_banned_rights") if isinstance(permissions, dict) else None
    )
    if not default_rights:
        warnings.append("No default banned rights were available in the blueprint.")

    steps.append(
        PlanStep(
            id="apply_default_permissions",
            action="apply_default_permissions",
            status="planned" if default_rights else "skipped",
            reason="Replicate default send/media/embed/poll/invite/pin/change-info permissions.",
            payload={"default_banned_rights": default_rights},
        )
    )


def add_forum_steps(
    steps: list[PlanStep],
    blueprint: dict[str, Any],
    warnings: list[str],
) -> None:
    forum = blueprint.get("forum", {})
    enabled = bool(forum.get("enabled")) if isinstance(forum, dict) else False
    topics = forum.get("topics", []) if isinstance(forum, dict) else []

    steps.append(
        PlanStep(
            id="configure_forum",
            action="configure_forum",
            status="planned" if enabled else "skipped",
            reason="Enable forum mode before topic creation when the source is a forum.",
            payload={
                "enabled": enabled,
                "tabs_enabled": bool(forum.get("tabs_enabled", False)),
                "topic_count": len(topics) if isinstance(topics, list) else 0,
            },
        )
    )

    if enabled and isinstance(topics, list):
        for index, topic in enumerate(topics, start=1):
            title = topic.get("title") if isinstance(topic, dict) else None
            steps.append(
                PlanStep(
                    id=f"create_topic_{index}",
                    action="create_forum_topic",
                    status="planned",
                    reason="Create forum topic metadata only; no topic messages are copied.",
                    payload={
                        "title": title,
                        "icon_color": topic.get("icon_color") if isinstance(topic, dict) else None,
                        "icon_emoji_id": topic.get("icon_emoji_id") if isinstance(topic, dict) else None,
                    },
                )
            )
    elif enabled:
        warnings.append("Forum is enabled, but topics were not exported as a list.")


def add_media_step(
    steps: list[PlanStep],
    blueprint: dict[str, Any],
    warnings: list[str],
) -> None:
    media = blueprint.get("configuration_media", {})
    has_photo_metadata = isinstance(media, dict) and bool(media.get("photo") or media.get("chat_photo"))
    assets = media.get("assets", []) if isinstance(media, dict) else []
    has_display_asset = any(
        isinstance(asset, dict) and asset.get("kind") == "display_photo" and asset.get("path")
        for asset in assets
    )
    status = "planned" if has_display_asset else "skipped"
    if has_photo_metadata and not has_display_asset:
        warnings.append("Configuration media metadata was detected, but no downloadable display photo asset is available.")

    steps.append(
        PlanStep(
            id="apply_configuration_media",
            action="apply_configuration_media",
            status=status,
            reason="Apply the downloaded source display photo to the destination.",
            payload=media if isinstance(media, dict) else {},
        )
    )


def collect_blocked_properties(
    blueprint: dict[str, Any],
    validation: ValidationResult,
) -> list[dict[str, Any]]:
    blocked: list[dict[str, Any]] = []
    unsupported = blueprint.get("unsupported_properties", [])
    if isinstance(unsupported, list):
        blocked.extend(item for item in unsupported if isinstance(item, dict))
    blocked.extend(
        {
            "path": issue.path,
            "reason": issue.message,
            "severity": issue.severity,
        }
        for issue in validation.issues
    )
    return blocked


def nested_get(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current
