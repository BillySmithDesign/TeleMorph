from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text


DEFAULT_BLUEPRINT_PATH = "blueprints/live-test.blueprint.json"
DEFAULT_PLAN_PATH = "plans/live-test.plan.json"
DEFAULT_APPLY_RESULT_PATH = "results/live-test.apply-result.json"
DEFAULT_VERIFICATION_PATH = "reports/live-test.verification.json"

console = Console()

TELEMORPH_BANNER = r"""
::::::::::: :::::::::: :::        :::::::::: ::::    ::::   ::::::::  :::::::::  :::::::::  :::    :::
    :+:     :+:        :+:        :+:        +:+:+: :+:+:+ :+:    :+: :+:    :+: :+:    :+: :+:    :+:
    +:+     +:+        +:+        +:+        +:+ +:+:+ +:+ +:+    +:+ +:+    +:+ +:+    +:+ +:+    +:+
    +#+     +#++:++#   +#+        +#++:++#   +#+  +:+  +#+ +#+    +:+ +#++:++#:  +#++:++#+  +#++:++#++
    +#+     +#+        +#+        +#+        +#+       +#+ +#+    +#+ +#+    +#+ +#+        +#+    +#+
    #+#     #+#        #+#        #+#        #+#       #+# #+#    #+# #+#    #+# #+#        #+#    #+#
    ###     ########## ########## ########## ###       ###  ########  ###    ### ###        ###    ###
""".strip("\n")


def header(subtitle: str | None = None) -> None:
    art = Text(TELEMORPH_BANNER, style="bold cyan")
    art.append("\nTelegram Structure Cloner", style="dim")
    if subtitle:
        art.append(f"\n{subtitle}", style="white")
    console.print()
    console.print(art, soft_wrap=True)
    console.rule(style="cyan")


def section(title: str) -> None:
    header(title.replace("TeleMorph ", ""))


def bullet(label: str, value: Any) -> None:
    console.print(f"[bold cyan]{label}:[/bold cyan] {value}")


def next_command(command: str) -> None:
    console.print(Panel(f"[bold]Next[/bold]\n[cyan]{command}[/cyan]", title="Continue", border_style="blue"))


def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def summary_table(title: str) -> Table:
    table = Table(title=title, box=box.ROUNDED, border_style="cyan", show_header=True)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")
    return table


def summarize_blueprint(blueprint: dict[str, Any]) -> None:
    source = blueprint.get("source", {})
    forum = blueprint.get("forum", {})
    permissions = blueprint.get("permissions", {})
    media = blueprint.get("configuration_media", {})
    assets = media.get("assets", []) if isinstance(media, dict) else []
    has_display_asset = any(isinstance(asset, dict) and asset.get("kind") == "display_photo" for asset in assets)
    unsupported = blueprint.get("unsupported_properties", [])

    table = summary_table("Blueprint Summary")
    table.add_row("Source", str(source.get("title") or "<untitled>"))
    table.add_row("Type", str(source.get("type") or "unknown"))
    table.add_row("Forum enabled", yes_no(bool(forum.get("enabled"))))
    table.add_row("Topics found", str(len(forum.get("topics", [])) if isinstance(forum.get("topics"), list) else 0))
    table.add_row("Default permissions", "captured" if permissions.get("default_banned_rights") else "not available")
    table.add_row("Config media", "detected" if media.get("photo") or media.get("chat_photo") else "not detected")
    table.add_row("Display photo asset", "ready" if has_display_asset else "not available")
    table.add_row("Unsupported notes", str(len(unsupported) if isinstance(unsupported, list) else 0))
    console.print(table)


def summarize_plan(plan: dict[str, Any]) -> None:
    steps = plan.get("steps", [])
    counts = Counter(step.get("status", "unknown") for step in steps if isinstance(step, dict))
    table = summary_table("Plan Summary")
    table.add_row("Destination", str(plan.get("destination_title") or "<untitled>"))
    table.add_row("Validation", "valid" if plan.get("validation", {}).get("valid") else "invalid")
    table.add_row("Steps", str(len(steps)))
    for status in ("planned", "skipped", "blocked", "unsupported", "failed"):
        if counts.get(status):
            table.add_row(status.capitalize(), str(counts[status]))
    console.print(table)
    print_warnings(plan.get("warnings", []))


def summarize_apply_result(result: dict[str, Any]) -> None:
    results = result.get("results", [])
    counts = Counter(item.get("status", "unknown") for item in results if isinstance(item, dict))
    destination = result.get("destination", {})
    table = summary_table("Apply Summary")
    table.add_row("Destination", str(destination.get("title") or destination.get("id") or "<unknown>"))
    for status in ("applied", "skipped", "unsupported", "failed"):
        table.add_row(status.capitalize(), str(counts.get(status, 0)))
    console.print(table)


def summarize_verification(report: dict[str, Any]) -> None:
    checks = report.get("checks", [])
    counts = Counter(item.get("status", "unknown") for item in checks if isinstance(item, dict))
    table = summary_table("Verification Summary")
    table.add_row("Passed", yes_no(bool(report.get("passed"))))
    table.add_row("Checks", str(len(checks)))
    table.add_row("Passed checks", str(counts.get("passed", 0)))
    table.add_row("Failed checks", str(counts.get("failed", 0)))
    console.print(table)


def print_warnings(warnings: list[Any]) -> None:
    if not warnings:
        return
    body = "\n".join(f"- {item}" for item in warnings)
    console.print(Panel(body, title="Warnings", border_style="yellow"))


def print_guided_help() -> None:
    header("Guided Help")
    console.print(flow_table())
    console.print(paths_table())
    console.print(
        Panel(
            "[bold green]Safe commands[/bold green]\n"
            "telemorph export\ntelemorph validate\ntelemorph plan\ntelemorph verify\n\n"
            "[bold red]Write command[/bold red]\ntelemorph apply --confirm",
            title="Command Safety",
            border_style="magenta",
        )
    )
    console.print("[dim]Run [bold]telemorph menu[/bold] for prompt-based buttons.[/dim]")


def print_menu() -> str:
    header("Command Menu")
    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("Choice", style="bold cyan", justify="right")
    table.add_column("Action", style="white")
    table.add_column("Command", style="dim")
    for number, action, command in menu_items():
        table.add_row(number, action, command)
    console.print(table)
    return Prompt.ask("Choose an action", choices=[item[0] for item in menu_items()], default="1")


def menu_items() -> list[tuple[str, str, str]]:
    return [
        ("1", "Export blueprint from Telegram", "telemorph export"),
        ("2", "Validate latest blueprint", "telemorph validate"),
        ("3", "Create dry-run plan", "telemorph plan"),
        ("4", "Apply plan and create clone", "telemorph apply --confirm"),
        ("5", "Verify latest clone result", "telemorph verify"),
        ("6", "Show guided help", "telemorph help"),
        ("7", "Exit", ""),
    ]


def flow_table() -> Table:
    table = Table(title="Recommended Flow", box=box.ROUNDED, border_style="cyan")
    table.add_column("Step", style="bold cyan", justify="right")
    table.add_column("Action")
    table.add_column("Command", style="bold white")
    rows = [
        ("1", "Read source structure", "telemorph export"),
        ("2", "Validate blueprint", "telemorph validate"),
        ("3", "Build dry-run plan", "telemorph plan"),
        ("4", "Review generated plan JSON", DEFAULT_PLAN_PATH),
        ("5", "Create clone", "telemorph apply --confirm"),
        ("6", "Verify result", "telemorph verify"),
    ]
    for row in rows:
        table.add_row(*row)
    return table


def paths_table() -> Table:
    table = Table(title="Default Files", box=box.ROUNDED, border_style="blue")
    table.add_column("Artifact", style="bold blue")
    table.add_column("Path")
    table.add_row("Blueprint", DEFAULT_BLUEPRINT_PATH)
    table.add_row("Plan", DEFAULT_PLAN_PATH)
    table.add_row("Apply result", DEFAULT_APPLY_RESULT_PATH)
    table.add_row("Verification", DEFAULT_VERIFICATION_PATH)
    return table


def yes_no(value: bool) -> str:
    return "[green]yes[/green]" if value else "[yellow]no[/yellow]"
