from __future__ import annotations

from pathlib import Path

from scripts.check_no_direct_streaming import find_violations


def test_api_routes_do_not_stream_files_directly() -> None:
    violations = find_violations(Path("app/api"))
    assert violations == []
