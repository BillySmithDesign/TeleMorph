from telegram_structure_cloner.planning import build_destination_plan
from telegram_structure_cloner.replication.results import ApplyResult, StepResult
from telegram_structure_cloner.verification.report import verify_apply_result

from .fixtures import sample_blueprint


def test_verify_apply_result_passes_when_steps_are_present():
    plan = build_destination_plan(sample_blueprint()).to_dict()
    apply_result = ApplyResult(
        generated_at="2026-09-24T00:00:00Z",
        destination={"id": 999},
        results=[
            StepResult(
                step_id=step["id"],
                action=step["action"],
                status="skipped" if step["id"] == "apply_settings" else "applied",
                message="ok",
            )
            for step in plan["steps"]
            if step["status"] == "planned"
        ],
    ).to_dict()

    report = verify_apply_result(plan, apply_result)

    assert report.passed is True


def test_verify_apply_result_fails_when_destination_is_missing():
    plan = build_destination_plan(sample_blueprint()).to_dict()
    apply_result = {"destination": {}, "results": []}

    report = verify_apply_result(plan, apply_result)

    assert report.passed is False
    assert any(check.path == "destination" for check in report.checks)
