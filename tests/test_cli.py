from telegram_structure_cloner.cli import build_parser
from telegram_structure_cloner.output import (
    DEFAULT_APPLY_RESULT_PATH,
    DEFAULT_BLUEPRINT_PATH,
    DEFAULT_PLAN_PATH,
    DEFAULT_VERIFICATION_PATH,
)


def test_parser_uses_telemorph_program_name():
    parser = build_parser()

    assert parser.prog == "telemorph"


def test_validate_uses_default_blueprint_path():
    args = build_parser().parse_args(["validate"])

    assert args.input == DEFAULT_BLUEPRINT_PATH


def test_plan_uses_default_paths():
    args = build_parser().parse_args(["plan"])

    assert args.input == DEFAULT_BLUEPRINT_PATH
    assert args.output == DEFAULT_PLAN_PATH


def test_apply_and_verify_use_default_paths():
    apply_args = build_parser().parse_args(["apply"])
    verify_args = build_parser().parse_args(["verify"])

    assert apply_args.input == DEFAULT_PLAN_PATH
    assert apply_args.output == DEFAULT_APPLY_RESULT_PATH
    assert verify_args.plan == DEFAULT_PLAN_PATH
    assert verify_args.result == DEFAULT_APPLY_RESULT_PATH
    assert verify_args.output == DEFAULT_VERIFICATION_PATH
