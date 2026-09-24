from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DialogChoice:
    index: int
    display_name: str
    entity: Any


async def choose_dialog(client: Any) -> Any:
    dialogs = await client.get_dialogs()
    choices = [
        DialogChoice(index=index, display_name=dialog.name or "<unnamed>", entity=dialog.entity)
        for index, dialog in enumerate(dialogs, start=1)
    ]

    if not choices:
        raise RuntimeError("No dialogs are available for this account.")

    for choice in choices:
        entity_type = type(choice.entity).__name__
        print(f"{choice.index:>3}. {choice.display_name} ({entity_type})")

    while True:
        raw_value = input("Select source dialog number: ").strip()
        try:
            selected = int(raw_value)
        except ValueError:
            print("Enter a number from the list.")
            continue

        for choice in choices:
            if choice.index == selected:
                return choice.entity

        print("That selection is not in the list.")


async def resolve_source(client: Any, source: str | None) -> Any:
    if source:
        return await client.get_entity(source)
    return await choose_dialog(client)
