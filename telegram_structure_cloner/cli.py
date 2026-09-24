from __future__ import annotations

import argparse
import asyncio

from .client import create_client
from .config import load_config
from .dialogs import resolve_source
from .inspection import inspect_source
from .planning import build_destination_plan
from .serialization import read_json, write_json
from .validation import validate_blueprint


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
