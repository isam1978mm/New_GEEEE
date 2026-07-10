from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import Settings
from app.services import storage
from app.services.run_history import RUN_STATUS_HISTORY_NAME, append_run_event


def test_write_json_atomic_replaces_file_without_temp_leftovers(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"

    storage.write_json_atomic(path, {"old": True}, indent=2, sort_keys=True)
    storage.write_json_atomic(path, {"new": True}, indent=2, sort_keys=True)

    assert json.loads(path.read_text(encoding="utf-8")) == {"new": True}
    assert list(tmp_path.glob(".manifest.json.*.tmp")) == []


def test_write_json_atomic_preserves_existing_file_when_replace_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "manifest.json"
    path.write_text('{"old": true}', encoding="utf-8")

    def fail_replace(_src: str | Path, _dst: str | Path) -> None:
        raise RuntimeError("forced replace failure")

    monkeypatch.setattr(storage.os, "replace", fail_replace)

    with pytest.raises(RuntimeError, match="forced replace failure"):
        storage.write_json_atomic(path, {"new": True}, indent=2, sort_keys=True)

    assert json.loads(path.read_text(encoding="utf-8")) == {"old": True}
    assert list(tmp_path.glob(".manifest.json.*.tmp")) == []


def test_run_history_append_uses_atomic_writer_without_temp_leftovers(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path, database_path=tmp_path / "test.db")

    append_run_event(settings, "run-1", "run_started")

    history_path = tmp_path / "runs" / "run-1" / RUN_STATUS_HISTORY_NAME
    assert history_path.is_file()
    assert json.loads(history_path.read_text(encoding="utf-8"))["events"][0]["event_type"] == "run_started"
    assert list(history_path.parent.glob(f".{RUN_STATUS_HISTORY_NAME}.*.tmp")) == []
