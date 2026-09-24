from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .blueprint import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    path: str
    message: str
    severity: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": [asdict(issue) for issue in self.issues],
        }


REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version": str,
    "exported_at": str,
    "source": dict,
    "settings": dict,
    "permissions": dict,
    "forum": dict,
    "configuration_media": dict,
    "unsupported_properties": list,
}

SUPPORTED_SOURCE_TYPES = {
    "channel",
    "group",
    "supergroup",
    "supergroup_forum",
    "channel_like",
}


def validate_blueprint(data: dict[str, Any]) -> ValidationResult:
    issues: list[ValidationIssue] = []

    for key, expected_type in REQUIRED_TOP_LEVEL_KEYS.items():
        if key not in data:
            issues.append(error(key, "Required key is missing."))
            continue
        if not isinstance(data[key], expected_type):
            issues.append(
                error(key, f"Expected {expected_type.__name__}, got {type(data[key]).__name__}.")
            )

    schema_version = data.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        issues.append(
            error(
                "schema_version",
                f"Unsupported schema version {schema_version!r}; expected {SCHEMA_VERSION!r}.",
            )
        )

    source = data.get("source")
    if isinstance(source, dict):
        source_type = source.get("type")
        if not source.get("title"):
            issues.append(error("source.title", "Source title is required for destination planning."))
        if source_type not in SUPPORTED_SOURCE_TYPES:
            issues.append(
                warning(
                    "source.type",
                    f"Source type {source_type!r} may not be supported by later replication.",
                )
            )

    forum = data.get("forum")
    if isinstance(forum, dict):
        if not isinstance(forum.get("enabled", False), bool):
            issues.append(error("forum.enabled", "Forum enabled flag must be a boolean."))
        topics = forum.get("topics", [])
        if not isinstance(topics, list):
            issues.append(error("forum.topics", "Forum topics must be a list."))

    unsupported = data.get("unsupported_properties")
    if isinstance(unsupported, list):
        for index, item in enumerate(unsupported):
            if not isinstance(item, dict):
                issues.append(error(f"unsupported_properties[{index}]", "Entry must be an object."))
                continue
            if not item.get("path") or not item.get("reason"):
                issues.append(
                    error(
                        f"unsupported_properties[{index}]",
                        "Entry must include both path and reason.",
                    )
                )

    return ValidationResult(
        valid=not any(issue.severity == "error" for issue in issues),
        issues=issues,
    )


def error(path: str, message: str) -> ValidationIssue:
    return ValidationIssue(path=path, message=message, severity="error")


def warning(path: str, message: str) -> ValidationIssue:
    return ValidationIssue(path=path, message=message, severity="warning")
