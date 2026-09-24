from pathlib import Path

from telegram_structure_cloner.media_assets import safe_name, sha256_file


def test_safe_name_keeps_artifact_paths_predictable():
    assert safe_name("Xp0sed - Leaks Clone!!") == "xp0sed-leaks-clone"


def test_sha256_file_hashes_bytes(tmp_path: Path):
    target = tmp_path / "asset.jpg"
    target.write_bytes(b"display-photo")

    assert sha256_file(target) == "7a2806b18917e7824ee41eddbcfbc8e4696b5408f426e286bdbed8f7541a89ba"
