from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "probe_campaign_014_openaltimetry.py"
)
SPEC = importlib.util.spec_from_file_location("campaign014_openaltimetry_probe", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_targets_are_exact_slide_rule_failures():
    assert [item["resource"] for item in MODULE.TARGETS] == [
        "ATL08_20210504235905_06291102_007_01.h5",
        "ATL08_20251226145703_01873002_007_01.h5",
    ]
    assert [item["track_id"] for item in MODULE.TARGETS] == [629, 187]
    assert [item["date"] for item in MODULE.TARGETS] == ["2021-05-04", "2025-12-26"]


def test_params_use_locked_campaign_bounds_and_public_api_shape():
    params = MODULE._params(MODULE.TARGETS[0], output_format="json")
    assert params == {
        "date": "2021-05-04",
        "minx": "-77.700000",
        "miny": "38.800000",
        "maxx": "-77.100000",
        "maxy": "39.200000",
        "trackId": "629",
        "outputFormat": "json",
        "client": "campaign014",
    }


def test_probe_writes_raw_json_and_reports_shape(tmp_path):
    captured: dict[str, object] = {}

    def fake_fetch(url: str, *, timeout_seconds: float):
        captured["url"] = url
        captured["timeout"] = timeout_seconds
        return 200, "application/json", b'{"series":[1,2,3],"status":"ok"}'

    result = MODULE.probe_target(
        MODULE.TARGETS[0],
        output_dir=tmp_path,
        timeout_seconds=17,
        output_format="json",
        fetch=fake_fetch,
    )

    parsed = urlparse(str(captured["url"]))
    query = parse_qs(parsed.query)
    assert parsed.path.endswith("/api/icesat2/atl08")
    assert query["date"] == ["2021-05-04"]
    assert query["trackId"] == ["629"]
    assert query["outputFormat"] == ["json"]
    assert captured["timeout"] == 17
    assert result["http_status"] == 200
    assert result["json_valid"] is True
    assert result["json_type"] == "dict"
    assert result["top_level_keys"] == ["series", "status"]
    raw_path = Path(str(result["raw_path"]))
    assert raw_path.is_file()
    assert json.loads(raw_path.read_text(encoding="utf-8"))["status"] == "ok"


def test_probe_can_store_csv_without_guessing_schema(tmp_path):
    body = b"latitude,longitude,height\n38.9,-77.4,100.2\n"

    def fake_fetch(url: str, *, timeout_seconds: float):
        return 200, "text/csv", body

    result = MODULE.probe_target(
        MODULE.TARGETS[1],
        output_dir=tmp_path,
        timeout_seconds=20,
        output_format="csv",
        fetch=fake_fetch,
    )

    assert result["bytes"] == len(body)
    assert result["content_type"] == "text/csv"
    assert Path(str(result["raw_path"])).read_bytes() == body
