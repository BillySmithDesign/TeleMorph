from __future__ import annotations

import argparse
import asyncio

from .client import create_client
from .config import load_config
from .dialogs import resolve_source
from .inspection import inspect_source
from .serialization import write_json


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telegram-structure-cloner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a read-only source blueprint.")
    export_parser.add_argument("--source", help="Username, invite link, ID, or dialog name.")
    export_parser.add_argument("--output", default="blueprint.json", help="Output JSON path.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "export":
        asyncio.run(export_blueprint(source=args.source, output=args.output))
