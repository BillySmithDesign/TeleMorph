from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class StepResult:
    step_id: str
    action: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ApplyResult:
    generated_at: str
    destination: dict[str, Any]
    results: list[StepResult]

    @classmethod
    def empty(cls) -> "ApplyResult":
        return cls(
            generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            destination={},
            results=[],
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["results"] = [asdict(item) for item in self.results]
        return data
