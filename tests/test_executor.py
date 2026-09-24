import pytest

from telegram_structure_cloner.planning import build_destination_plan
from telegram_structure_cloner.replication.executor import apply_plan

from .fixtures import sample_blueprint


class FakeAdapter:
    async def create_destination(self, payload):
        return {"id": 999, "title": payload["title"], "raw_class": "FakeChannel"}

    async def apply_destination_settings(self, payload):
        return {"about_applied": False, "noop": True, "reason": "Already unchanged."}

    async def apply_default_permissions(self, payload):
        return {"permissions_applied": bool(payload.get("default_banned_rights"))}

    async def configure_forum(self, payload):
        return {"forum_enabled": payload["enabled"]}

    async def create_forum_topic(self, payload):
        return {"topic_title": payload["title"]}

    async def apply_configuration_media(self, payload):
        return {"media_applied": True, "metadata_present": bool(payload)}


@pytest.mark.asyncio
async def test_apply_plan_runs_planned_steps():
    plan = build_destination_plan(sample_blueprint()).to_dict()

    result = await apply_plan(plan, FakeAdapter())
    serialized = result.to_dict()

    assert serialized["destination"]["id"] == 999
    assert {item["status"] for item in serialized["results"]} == {"applied", "skipped"}
    assert serialized["results"][0]["action"] == "create_destination"


@pytest.mark.asyncio
async def test_apply_plan_rejects_invalid_plan():
    plan = build_destination_plan(sample_blueprint()).to_dict()
    plan["validation"]["valid"] = False

    with pytest.raises(ValueError, match="failed validation"):
        await apply_plan(plan, FakeAdapter())
