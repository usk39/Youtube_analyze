from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def save_snapshot(data_dir: Path, name: str, data: dict) -> Path:
    snap_dir = Path(data_dir) / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    history_path = snap_dir / f"{name}_{timestamp}.json"
    history_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    latest_path = snap_dir / f"latest_{name}.json"
    latest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return history_path


def load_latest_snapshot(data_dir: Path, name: str) -> dict | None:
    latest_path = Path(data_dir) / "snapshots" / f"latest_{name}.json"
    if not latest_path.exists():
        return None
    return json.loads(latest_path.read_text(encoding="utf-8"))
