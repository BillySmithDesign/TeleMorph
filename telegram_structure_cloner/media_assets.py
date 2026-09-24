from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


DEFAULT_ASSET_DIR = "assets/config_media"


async def download_config_photo(client: Any, entity: Any, asset_dir: str = DEFAULT_ASSET_DIR) -> dict[str, Any] | None:
    output_dir = Path(asset_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = safe_name(getattr(entity, "title", None) or str(getattr(entity, "id", "source")))
    target = output_dir / f"{base_name}-display-photo.jpg"

    result = await client.download_profile_photo(entity, file=str(target), download_big=True)
    if not result:
        return None

    path = Path(result)
    return {
        "kind": "display_photo",
        "path": str(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "content_type": "image/jpeg",
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() else "-" for char in value.strip().lower())
    collapsed = "-".join(part for part in cleaned.split("-") if part)
    return collapsed[:80] or "source"
