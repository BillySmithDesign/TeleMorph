from telegram_structure_cloner.planning import build_destination_plan

from .fixtures import sample_blueprint


def test_plan_is_dry_run_and_creates_expected_steps():
    plan = build_destination_plan(sample_blueprint(), destination_title="Planned Clone")
    serialized = plan.to_dict()

    assert serialized["dry_run"] is True
    assert serialized["destination_title"] == "Planned Clone"
    assert serialized["validation"]["valid"] is True
    assert [step["id"] for step in serialized["steps"]] == [
        "create_destination",
        "apply_settings",
        "apply_default_permissions",
        "configure_forum",
        "create_topic_1",
        "apply_configuration_media",
    ]
    assert serialized["steps"][0]["payload"]["copy_messages"] is False
    assert serialized["steps"][0]["payload"]["copy_members"] is False


def test_invalid_blueprint_blocks_all_steps():
    blueprint = sample_blueprint()
    blueprint["schema_version"] = "0.0.1"

    plan = build_destination_plan(blueprint)
    serialized = plan.to_dict()

    assert serialized["validation"]["valid"] is False
    assert {step["status"] for step in serialized["steps"]} == {"blocked"}
    assert any(item["path"] == "schema_version" for item in serialized["blocked_properties"])
