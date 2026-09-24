from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class VerificationCheck:
    path: str
    status: str
    message: str


@dataclass(frozen=True, slots=True)
class VerificationReport:
    generated_at: str
    passed: bool
    checks: list[VerificationCheck]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "passed": self.passed,
            "checks": [asdict(check) for check in self.checks],
        }


def verify_apply_result(plan: dict[str, Any], apply_result: dict[str, Any]) -> VerificationReport:
    checks: list[VerificationCheck] = []
    expected_steps = [
        step for step in plan.get("steps", []) if isinstance(step, dict) and step.get("status") == "planned"
    ]
    results = apply_result.get("results", [])
    result_by_step = {
        item.get("step_id"): item
        for item in results
        if isinstance(item, dict) and item.get("step_id")
    }

    for step in expected_steps:
        step_id = step.get("id")
        result = result_by_step.get(step_id)
        if result is None:
            checks.append(
                VerificationCheck(
                    path=f"steps.{step_id}",
                    status="failed",
                    message="Planned step is missing from apply result.",
                )
            )
            continue
        if result.get("status") not in {"applied", "unsupported"}:
            checks.append(
                VerificationCheck(
                    path=f"steps.{step_id}",
                    status="failed",
                    message=f"Step result status is {result.get('status')!r}.",
                )
            )
            continue
        checks.append(
            VerificationCheck(
                path=f"steps.{step_id}",
                status="passed",
                message=f"Step completed with status {result.get('status')}.",
            )
        )

    destination = apply_result.get("destination", {})
    if not destination:
        checks.append(
            VerificationCheck(
                path="destination",
                status="failed",
                message="Apply result does not contain destination identity.",
            )
        )
    else:
        checks.append(
            VerificationCheck(
                path="destination",
                status="passed",
                message="Apply result contains destination identity.",
            )
        )

    return VerificationReport(
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        passed=not any(check.status == "failed" for check in checks),
        checks=checks,
    )
