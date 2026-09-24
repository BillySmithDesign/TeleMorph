from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "1.0.0"


@dataclass(slots=True)
class UnsupportedProperty:
    path: str
    reason: str
    severity: str = "info"


@dataclass(slots=True)
class Blueprint:
    schema_version: str
    exported_at: str
    source: dict[str, Any]
    settings: dict[str, Any]
    permissions: dict[str, Any]
    forum: dict[str, Any]
    configuration_media: dict[str, Any]
    unsupported_properties: list[UnsupportedProperty] = field(default_factory=list)

    @classmethod
    def empty(cls) -> "Blueprint":
        return cls(
            schema_version=SCHEMA_VERSION,
            exported_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source={},
            settings={},
            permissions={},
            forum={"enabled": False, "topics": []},
            configuration_media={},
            unsupported_properties=[],
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["unsupported_properties"] = [asdict(item) for item in self.unsupported_properties]
        return data

    def add_unsupported(self, path: str, reason: str, severity: str = "info") -> None:
        self.unsupported_properties.append(
            UnsupportedProperty(path=path, reason=reason, severity=severity)
        )
