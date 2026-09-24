from __future__ import annotations

import argparse
import asyncio
from typing import Any

from .client import create_client
from .config import load_config
from .dialogs import resolve_source
from .inspection import inspect_source
from .output import (
    DEFAULT_APPLY_RESULT_PATH,
    DEFAULT_BLUEPRINT_PATH,
    DEFAULT_PLAN_PATH,
    DEFAULT_VERIFICATION_PATH,
    ensure_parent,
    next_command,
    print_guided_help,
    print_menu,
    section,
    summarize_apply_result,
    summarize_blueprint,
    summarize_plan,
    summarize_verification,
)
from .planning import build_destination_plan
from .replication.adapter import TelethonDestinationAdapter
from .replication.executor import apply_plan
from .serialization import read_json, write_json
from .validation import validate_blueprint
from .verification.report import verify_apply_result


async def export_blueprint(source: str | None, output: str, asset_dir: str) -> None:
    section("TeleMorph Export")
    config = load_config()
    client = create_client(config)
    async with client:
        if not await client.is_user_authorized():
            print("Telegram login required. Follow the prompts from Telethon.")
            await client.start()
        entity = await resolve_source(client, source)
        print("Inspecting source structure. No messages or members will be copied.")
        blueprint = await inspect_source(client, entity, asset_dir=asset_dir)
        ensure_parent(output)
        write_json(output, blueprint.to_dict())
        summarize_blueprint(blueprint.to_dict())
        print()
        print(f"Blueprint written: {output}")
        next_command(f"telemorph validate {output}")


def validate_blueprint_file(input_path: str) -> int:
    section("TeleMorph Validate")
    blueprint = read_json(input_path)
    result = validate_blueprint(blueprint)
    for issue in result.issues:
        print(f"{issue.severity.upper()}: {issue.path}: {issue.message}")
    if result.valid:
        summarize_blueprint(blueprint)
        print()
        print(f"Blueprint is valid: {input_path}")
        next_command(f"telemorph plan {input_path}")
        return 0
    print(f"Blueprint is invalid: {input_path}")
    return 1


def plan_destination(input_path: str, output: str, destination_title: str | None) -> int:
    section("TeleMorph Plan")
    blueprint = read_json(input_path)
    plan = build_destination_plan(blueprint, destination_title=destination_title)
    ensure_parent(output)
    write_json(output, plan.to_dict())
    summarize_plan(plan.to_dict())
    print()
    print(f"Dry-run plan written: {output}")
    if not plan.validation["valid"]:
        print("Plan contains blocked steps because blueprint validation failed.")
        return 1
    next_command(f"Review {output}, then run: telemorph apply {output} --confirm")
    return 0


async def apply_destination_plan(input_path: str, output: str, confirm: bool) -> int:
    section("TeleMorph Apply")
    if not confirm:
        print("Refusing to apply plan without --confirm.")
        print("This command can create or modify a Telegram destination.")
        return 2

    plan = read_json(input_path)
    summarize_plan(plan)
    config = load_config()
    client = create_client(config)
    async with client:
        if not await client.is_user_authorized():
            print("Telegram login required. Follow the prompts from Telethon.")
            await client.start()
        duplicate = await destination_title_exists(client, plan.get("destination_title"))
        if duplicate:
            print(f"Warning: a dialog named {plan.get('destination_title')!r} already exists.")
        adapter = TelethonDestinationAdapter(client)
        result = await apply_plan(plan, adapter)
        ensure_parent(output)
        write_json(output, result.to_dict())
        summarize_apply_result(result.to_dict())
        print()
        print(f"Apply result written: {output}")
        failed = [item for item in result.results if item.status == "failed"]
        next_command(f"telemorph verify {input_path} {output}")
        return 1 if failed else 0


def verify_result(plan_path: str, result_path: str, output: str) -> int:
    section("TeleMorph Verify")
    plan = read_json(plan_path)
    apply_result = read_json(result_path)
    report = verify_apply_result(plan, apply_result)
    ensure_parent(output)
    write_json(output, report.to_dict())
    summarize_verification(report.to_dict())
    print()
    print(f"Verification report written: {output}")
    return 0 if report.passed else 1


async def destination_title_exists(client: Any, title: str | None) -> bool:
    if not title:
        return False
    dialogs = await client.get_dialogs()
    return any(getattr(dialog, "name", None) == title for dialog in dialogs)


async def run_menu() -> int:
    choice = print_menu()
    if choice == "1":
        await export_blueprint(source=None, output=DEFAULT_BLUEPRINT_PATH)
        return 0
    if choice == "2":
        return validate_blueprint_file(DEFAULT_BLUEPRINT_PATH)
    if choice == "3":
        return plan_destination(DEFAULT_BLUEPRINT_PATH, DEFAULT_PLAN_PATH, None)
    if choice == "4":
        return await apply_destination_plan(DEFAULT_PLAN_PATH, DEFAULT_APPLY_RESULT_PATH, True)
    if choice == "5":
        return verify_result(DEFAULT_PLAN_PATH, DEFAULT_APPLY_RESULT_PATH, DEFAULT_VERIFICATION_PATH)
    if choice == "6":
        print_guided_help()
        return 0
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telemorph")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("help", help="Show the guided TeleMorph workflow.")
    subparsers.add_parser("menu", help="Show prompt-based flow buttons.")

    export_parser = subparsers.add_parser("export", help="Export a read-only source blueprint.")
    export_parser.add_argument("--source", help="Username, invite link, ID, or dialog name.")
    export_parser.add_argument("--output", default=DEFAULT_BLUEPRINT_PATH, help="Output JSON path.")
    export_parser.add_argument("--asset-dir", default="assets/config_media", help="Config media asset folder.")

    validate_parser = subparsers.add_parser("validate", help="Validate a blueprint JSON file.")
    validate_parser.add_argument("input", nargs="?", default=DEFAULT_BLUEPRINT_PATH, help="Blueprint JSON path.")

    plan_parser = subparsers.add_parser("plan", help="Create a dry-run destination plan.")
    plan_parser.add_argument("input", nargs="?", default=DEFAULT_BLUEPRINT_PATH, help="Blueprint JSON path.")
    plan_parser.add_argument("--output", default=DEFAULT_PLAN_PATH, help="Output plan JSON path.")
    plan_parser.add_argument("--destination-title", help="Override planned destination title.")

    apply_parser = subparsers.add_parser("apply", help="Apply a destination plan to Telegram.")
    apply_parser.add_argument("input", nargs="?", default=DEFAULT_PLAN_PATH, help="Plan JSON path.")
    apply_parser.add_argument("--output", default=DEFAULT_APPLY_RESULT_PATH, help="Output result JSON path.")
    apply_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required. Confirms this command may create or modify a destination.",
    )

    verify_parser = subparsers.add_parser("verify", help="Verify a plan against an apply result.")
    verify_parser.add_argument("plan", nargs="?", default=DEFAULT_PLAN_PATH, help="Plan JSON path.")
    verify_parser.add_argument(
        "result",
        nargs="?",
        default=DEFAULT_APPLY_RESULT_PATH,
        help="Apply result JSON path.",
    )
    verify_parser.add_argument("--output", default=DEFAULT_VERIFICATION_PATH, help="Output report JSON path.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "help":
        print_guided_help()
    elif args.command == "menu":
        raise SystemExit(asyncio.run(run_menu()))
    elif args.command == "export":
        asyncio.run(export_blueprint(source=args.source, output=args.output, asset_dir=args.asset_dir))
    elif args.command == "validate":
        raise SystemExit(validate_blueprint_file(args.input))
    elif args.command == "plan":
        raise SystemExit(
            plan_destination(
                input_path=args.input,
                output=args.output,
                destination_title=args.destination_title,
            )
        )
    elif args.command == "apply":
        raise SystemExit(
            asyncio.run(
                apply_destination_plan(
                    input_path=args.input,
                    output=args.output,
                    confirm=args.confirm,
                )
            )
        )
    elif args.command == "verify":
        raise SystemExit(
            verify_result(
                plan_path=args.plan,
                result_path=args.result,
                output=args.output,
            )
        )
