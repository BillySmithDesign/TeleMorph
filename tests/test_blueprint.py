from telegram_structure_cloner.blueprint import Blueprint, SCHEMA_VERSION


def test_blueprint_defaults_are_versioned():
    blueprint = Blueprint.empty()

    assert blueprint.schema_version == SCHEMA_VERSION
    assert blueprint.forum == {"enabled": False, "topics": []}
    assert blueprint.to_dict()["unsupported_properties"] == []


def test_unsupported_properties_are_serialized():
    blueprint = Blueprint.empty()
    blueprint.add_unsupported("settings.example", "Not available")

    serialized = blueprint.to_dict()

    assert serialized["unsupported_properties"] == [
        {"path": "settings.example", "reason": "Not available", "severity": "info"}
    ]
