from telegram_structure_cloner.validation import validate_blueprint

from .fixtures import sample_blueprint


def test_valid_blueprint_passes_validation():
    result = validate_blueprint(sample_blueprint())

    assert result.valid is True
    assert result.issues == []


def test_missing_required_key_fails_validation():
    blueprint = sample_blueprint()
    del blueprint["source"]

    result = validate_blueprint(blueprint)

    assert result.valid is False
    assert any(issue.path == "source" for issue in result.issues)


def test_unknown_source_type_is_warning_not_failure():
    blueprint = sample_blueprint()
    blueprint["source"]["type"] = "mystery"

    result = validate_blueprint(blueprint)

    assert result.valid is True
    assert any(issue.path == "source.type" and issue.severity == "warning" for issue in result.issues)
