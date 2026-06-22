from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.roi_contract import ROI_CONTRACT_RELATIVE_PATH, ROI_CONTRACT_SCHEMA


def test_create_run_writes_private_roi_contract_without_public_exposure(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir))
        _upgrade_database(settings)
        monkeypatch.setattr("app.api.runs.enqueue_core_pipeline_run", _no_background_run)

        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            create_response = client.post("/runs", json={"lat": 35.59499, "lon": 36.12694, "name": "safe-run"})

            assert create_response.status_code == 201
            run_id = create_response.json()["id"]
            detail_response = client.get(f"/runs/{run_id}")
            outputs_response = client.get(f"/runs/{run_id}/outputs")

        contract_path = settings.data_dir / "runs" / run_id / ROI_CONTRACT_RELATIVE_PATH
        assert contract_path.is_file()
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        assert contract["schema"] == ROI_CONTRACT_SCHEMA
        assert contract["selected_point"]["latitude"] == 35.59499
        assert contract["selected_point"]["longitude"] == 36.12694
        assert contract["roi_15km_wgs84_approx"]["side_length_km"] == 15.0
        assert contract["roi_6_4km_utm"]["side_length_m"] == 6400.0
        assert contract["grid"]["scale_m"] == 10
        assert contract["grid"]["size_px"] == 640
        assert contract["privacy"]["public_api_exposure"] == "forbidden"
        assert contract["privacy"]["operator_output_listing"] == "forbidden"

        for response in (create_response, detail_response, outputs_response):
            assert response.status_code < 400
            lowered = response.text.casefold()
            assert "run_roi_contract" not in lowered
            assert "private/" not in lowered
            assert "selected_point" not in lowered
            assert "roi_15km" not in lowered
            assert "roi_6_4km" not in lowered
            assert "latitude" not in lowered
            assert "longitude" not in lowered
            assert "bounds" not in lowered
            assert "transform" not in lowered

        output_paths = {item["relative_path"] for item in outputs_response.json()["outputs"]}
        assert ROI_CONTRACT_RELATIVE_PATH not in output_paths


def _no_background_run(*args, **kwargs) -> None:
    return None


def _settings(root: Path) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(data_dir=data_dir, database_path=data_dir / "gee_screening.db")


def _upgrade_database(settings: Settings) -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+aiosqlite", ""))
    command.upgrade(cfg, "head")
