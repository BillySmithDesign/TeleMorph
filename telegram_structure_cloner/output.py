from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_BLUEPRINT_PATH = "blueprints/live-test.blueprint.json"
DEFAULT_PLAN_PATH = "plans/live-test.plan.json"
DEFAULT_APPLY_RESULT_PATH = "results/live-test.apply-result.json"
DEFAULT_VERIFICATION_PATH = "reports/live-test.verification.json"


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def bullet(label: str, value: Any) -> None:
    print(f"{label}: {value}")


def next_command(command: str) -> None:
    print()
    print("Next:")
    print(command)


def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def summarize_blueprint(blueprint: dict[str, Any]) -> None:
    source = blueprint.get("source", {})
    forum = blueprint.get("forum", {})
    permissions = blueprint.get("permissions", {})
    media = blueprint.get("configuration_media", {})
    unsupported = blueprint.get("unsupported_properties", [])

    section("Blueprint Summary")
    bullet("Source", source.get("title") or "<untitled>")
    bullet("Type", source.get("type") or "unknown")
    bullet("Forum enabled", bool(forum.get("enabled")))
    bullet("Topics found", len(forum.get("topics", [])) if isinstance(forum.get("topics"), list) else 0)
    bullet("Default permissions", "captured" if permissions.get("default_banned_rights") else "not available")
    bullet("Config media", "detected" if media.get("photo") or media.get("chat_photo") else "not detected")
    bullet("Unsupported notes", len(unsupported) if isinstance(unsupported, list) else 0)


def summarize_plan(plan: dict[str, Any]) -> None:
    steps = plan.get("steps", [])
    counts = Counter(step.get("status", "unknown") for step in steps if isinstance(step, dict))
    section("Plan Summary")
    bullet("Destination", plan.get("destination_title") or "<untitled>")
    bullet("Validation", "valid" if plan.get("validation", {}).get("valid") else "invalid")
    bullet("Steps", len(steps))
    for status in ("planned", "skipped", "blocked", "unsupported", "failed"):
        if counts.get(status):
            bullet(status.capitalize(), counts[status])
    warnings = plan.get("warnings", [])
    if warnings:
        print()
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")


def summarize_apply_result(result: dict[str, Any]) -> None:
    results = result.get("results", [])
    counts = Counter(item.get("status", "unknown") for item in results if isinstance(item, dict))
    section("Apply Summary")
    destination = result.get("destination", {})
    bullet("Destination", destination.get("title") or destination.get("id") or "<unknown>")
    for status in ("applied", "skipped", "unsupported", "failed"):
        bullet(status.capitalize(), counts.get(status, 0))


def summarize_verification(report: dict[str, Any]) -> None:
    checks = report.get("checks", [])
    counts = Counter(item.get("status", "unknown") for item in checks if isinstance(item, dict))
    section("Verification Summary")
    bullet("Passed", bool(report.get("passed")))
    bullet("Checks", len(checks))
    bullet("Passed checks", counts.get("passed", 0))
    bullet("Failed checks", counts.get("failed", 0))


def print_guided_help() -> None:
    section("TeleMorph Help")
    print("Guided flow:")
    print("1. telemorph export")
    print("2. telemorph validate")
    print("3. telemorph plan")
    print("4. Review the generated plan JSON")
    print("5. telemorph apply --confirm")
    print("6. telemorph verify")
    print()
    print("Default paths:")
    bullet("Blueprint", DEFAULT_BLUEPRINT_PATH)
    bullet("Plan", DEFAULT_PLAN_PATH)
    bullet("Apply result", DEFAULT_APPLY_RESULT_PATH)
    bullet("Verification", DEFAULT_VERIFICATION_PATH)
    print()
    print("Safe commands:")
    print("telemorph export")
    print("telemorph validate")
    print("telemorph plan")
    print("telemorph verify")
    print()
    print("Write command:")
    print("telemorph apply --confirm")
