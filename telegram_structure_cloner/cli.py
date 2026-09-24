from __future__ import annotations

import argparse
import asyncio

from .client import create_client
from .config import load_config
from .dialogs import resolve_source
from .inspection import inspect_source
from .planning import build_destination_plan
from .replication.adapter import TelethonDestinationAdapter
from .replication.executor import apply_plan
from .serialization import read_json, write_json
from .validation import validate_blueprint
from .verification.report import verify_apply_result


async def export_blueprint(source: str | None, output: str) -> None:
    config = load_config()
    client = create_client(config)
    async with client:
        if not await client.is_user_authorized():
            print("Telegram login required. Follow the prompts from Telethon.")
            await client.start()
        entity = await resolve_source(client, source)
        blueprint = await inspect_source(client, entity)
        write_json(output, blueprint.to_dict())
        print(f"Exported blueprint to {output}")


def validate_blueprint_file(input_path: str) -> int:
    blueprint = read_json(input_path)
    result = validate_blueprint(blueprint)
    for issue in result.issues:
        print(f"{issue.severity.upper()}: {issue.path}: {issue.message}")
    if result.valid:
        print(f"Blueprint is valid: {input_path}")
        return 0
    print(f"Blueprint is invalid: {input_path}")
    return 1


def plan_destination(input_path: str, output: str, destination_title: str | None) -> int:
    blueprint = read_json(input_path)
    plan = build_destination_plan(blueprint, destination_title=destination_title)
    write_json(output, plan.to_dict())
    print(f"Wrote dry-run destination plan to {output}")
    if not plan.validation["valid"]:
        print("Plan contains blocked steps because blueprint validation failed.")
        return 1
    return 0


async def apply_destination_plan(input_path: str, output: str, confirm: bool) -> int:
    if not confirm:
        print("Refusing to apply plan without --confirm.")
        return 2

    plan = read_json(input_path)
    config = load_config()
    client = create_client(config)
    async with client:
        if not await client.is_user_authorized():
            print("Telegram login required. Follow the prompts from Telethon.")
            await client.start()
        adapter = TelethonDestinationAdapter(client)
        result = await apply_plan(plan, adapter)
        write_json(output, result.to_dict())
        print(f"Wrote apply result to {output}")
        failed = [item for item in result.results if item.status == "failed"]
        return 1 if failed else 0


def verify_result(plan_path: str, result_path: str, output: str) -> int:
    plan = read_json(plan_path)
    apply_result = read_json(result_path)
    report = verify_apply_result(plan, apply_result)
    write_json(output, report.to_dict())
    print(f"Wrote verification report to {output}")
    return 0 if report.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telegram-structure-cloner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a read-only source blueprint.")
    export_parser.add_argument("--source", help="Username, invite link, ID, or dialog name.")
    export_parser.add_argument("--output", default="blueprint.json", help="Output JSON path.")

    validate_parser = subparsers.add_parser("validate", help="Validate a blueprint JSON file.")
    validate_parser.add_argument("input", help="Blueprint JSON path.")

    plan_parser = subparsers.add_parser("plan", help="Create a dry-run destination plan.")
    plan_parser.add_argument("input", help="Blueprint JSON path.")
    plan_parser.add_argument("--output", default="plan.json", help="Output plan JSON path.")
    plan_parser.add_argument("--destination-title", help="Override planned destination title.")

    apply_parser = subparsers.add_parser("apply", help="Apply a destination plan to Telegram.")
    apply_parser.add_argument("input", help="Plan JSON path.")
    apply_parser.add_argument("--output", default="apply-result.json", help="Output result JSON path.")
    apply_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required. Confirms this command may create or modify a destination.",
    )

    verify_parser = subparsers.add_parser("verify", help="Verify a plan against an apply result.")
    verify_parser.add_argument("plan", help="Plan JSON path.")
    verify_parser.add_argument("result", help="Apply result JSON path.")
    verify_parser.add_argument("--output", default="verification.json", help="Output report JSON path.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "export":
        asyncio.run(export_blueprint(source=args.source, output=args.output))
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
