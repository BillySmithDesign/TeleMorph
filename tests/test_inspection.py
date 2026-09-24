from types import SimpleNamespace

import pytest

from telegram_structure_cloner.inspection import inspect_source


class FakeClient:
    def __init__(self):
        self.calls = []

    async def __call__(self, request):
        self.calls.append(type(request).__name__)
        raise RuntimeError("network disabled in tests")


@pytest.mark.asyncio
async def test_inspection_never_requires_messages_or_members_for_basic_entity():
    entity = SimpleNamespace(
        id=123,
        title="Source Group",
        username="source_group",
        forum=False,
        default_banned_rights=SimpleNamespace(send_messages=False),
        photo=SimpleNamespace(photo_id=456),
    )

    blueprint = await inspect_source(FakeClient(), entity)
    serialized = blueprint.to_dict()

    assert serialized["source"]["title"] == "Source Group"
    assert serialized["source"]["id"] == 123
    assert serialized["permissions"]["default_banned_rights"]["send_messages"] is False
    assert serialized["configuration_media"]["photo"]["photo_id"] == 456
    assert any(item["path"] == "members" for item in serialized["unsupported_properties"])
    assert any(item["path"] == "messages" for item in serialized["unsupported_properties"])


@pytest.mark.asyncio
async def test_forum_topic_failure_is_reported():
    entity = SimpleNamespace(id=123, title="Forum", forum=True)

    blueprint = await inspect_source(FakeClient(), entity)
    serialized = blueprint.to_dict()

    assert serialized["forum"]["enabled"] is True
    assert any(item["path"] == "forum.topics" for item in serialized["unsupported_properties"])
