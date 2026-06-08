from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.pipeline.parity.private_map_artifact_comparator import (
    PHASE_D1_GEOJSON_FAMILY_ID,
    PHASE_D2_KMZ_FAMILY_ID,
    PHASE_D3_HEATMAP_FAMILY_ID,
)
from app.pipeline.parity.private_map_artifact_writers import (
    write_private_geojson_feature_collection,
    write_private_heatmap_json,
    write_private_kmz_points,
)
from app.services.storage import get_run_dir

_RUN_ID = "run_authorized"
_PATH = f"/runs/{_RUN_ID}/operator/private-overlays"


def _settings(
    root: Path,
    *,
    enabled: bool,
    trusted_proxy_enabled: bool | None = None,
) -> Settings:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        data_dir=data_dir,
        database_path=data_dir / "gee_screening.db",
        operator_private_overlay_preview_enabled=enabled,
        operator_auth_trusted_proxy_enabled=enabled if trusted_proxy_enabled is None else trusted_proxy_enabled,
    )


def _upgrade_database(settings: Settings) -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+aiosqlite", ""))
    command.upgrade(cfg, "head")


def _write_artifacts(settings: Settings, run_id: str = _RUN_ID) -> None:
    run_dir = get_run_dir(settings, run_id)
    write_private_geojson_feature_collection(
        run_dir=run_dir,
        features=[
            {
                "type": "Feature",
                "properties": {"class_label": "Class_1"},
                "geometry": {"type": "Point", "coordinates": [36.1, 35.2]},
            }
        ],
    )
    write_private_kmz_points(run_dir=run_dir, points=[{"id": "p1", "latitude": 35.2, "longitude": 36.1}])
    write_private_heatmap_json(
        run_dir=run_dir,
        points=[{"id": "h1", "latitude": 35.2, "longitude": 36.1, "weight": 0.5}],
    )


def _operator_headers(*, authenticated: bool = True, roles: str = "operator", authorized_runs: str = _RUN_ID) -> dict[str, str]:
    return {
        "X-Operator-Authenticated": "true" if authenticated else "false",
        "X-Operator-Id": "operator_1",
        "X-Operator-Roles": roles,
        "X-Operator-Authorized-Runs": authorized_runs,
        "X-Request-Id": "req_test",
    }


def test_route_is_disabled_by_default() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=False)
        _upgrade_database(settings)
        _write_artifacts(settings)
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get(
                _PATH,
                params={"artifact_family": PHASE_D1_GEOJSON_FAMILY_ID},
                headers=_operator_headers(),
            )
    assert response.status_code == 403
    body = response.json()
    assert body["outcome"] == "denied"
    assert "run_id" not in body
    assert "artifact_family" not in body
    assert "preview_payload" not in body


def test_unauthenticated_actor_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _upgrade_database(settings)
        _write_artifacts(settings)
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get(
                _PATH,
                params={"artifact_family": PHASE_D1_GEOJSON_FAMILY_ID},
                headers=_operator_headers(authenticated=False),
            )
    assert response.status_code == 403
    assert response.json()["outcome"] == "denied"


def test_non_operator_actor_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _upgrade_database(settings)
        _write_artifacts(settings)
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get(
                _PATH,
                params={"artifact_family": PHASE_D1_GEOJSON_FAMILY_ID},
                headers=_operator_headers(roles="viewer"),
            )
    assert response.status_code == 403


def test_unauthorized_run_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _upgrade_database(settings)
        _write_artifacts(settings)
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get(
                _PATH,
                params={"artifact_family": PHASE_D1_GEOJSON_FAMILY_ID},
                headers=_operator_headers(authorized_runs="other_run"),
            )
    assert response.status_code == 403


def test_unsupported_artifact_family_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _upgrade_database(settings)
        _write_artifacts(settings)
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get(
                _PATH,
                params={"artifact_family": "public_overlay_any"},
                headers=_operator_headers(),
            )
    assert response.status_code == 403


def test_public_modes_denied() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _upgrade_database(settings)
        _write_artifacts(settings)
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            for mode in ("redacted_public", "public_exact_coordinate", "unknown_mode"):
                response = client.get(
                    _PATH,
                    params={"artifact_family": PHASE_D1_GEOJSON_FAMILY_ID, "access_mode": mode},
                    headers=_operator_headers(),
                )
                assert response.status_code == 403, mode


def test_trusted_proxy_disabled_denies_even_with_operator_headers() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True, trusted_proxy_enabled=False)
        _upgrade_database(settings)
        _write_artifacts(settings)
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get(
                _PATH,
                params={"artifact_family": PHASE_D1_GEOJSON_FAMILY_ID},
                headers=_operator_headers(),
            )
    assert response.status_code == 403
    body = response.json()
    assert body["outcome"] == "denied"
    assert "preview_payload" not in body
    assert "run_id" not in body
    assert "artifact_family" not in body
    _assert_no_public_surface(response.text, settings)


def test_valid_operator_preview_allowed_for_each_family() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _upgrade_database(settings)
        _write_artifacts(settings)
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            for family, preview_type in (
                (PHASE_D1_GEOJSON_FAMILY_ID, "geojson_feature_collection"),
                (PHASE_D2_KMZ_FAMILY_ID, "kmz_placemarks"),
                (PHASE_D3_HEATMAP_FAMILY_ID, "heatmap_points"),
            ):
                response = client.get(
                    _PATH,
                    params={"artifact_family": family},
                    headers=_operator_headers(),
                )
                assert response.status_code == 200, family
                body = response.json()
                assert body["outcome"] == "allowed"
                assert body["preview_type"] == preview_type
                assert body["frontend_visible"] == "operator_only"
                assert body["downloadable_via_api"] is False
                _assert_no_public_surface(response.text, settings)


def test_authorized_missing_artifact_returns_not_available() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _upgrade_database(settings)
        # no artifacts written
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            response = client.get(
                _PATH,
                params={"artifact_family": PHASE_D1_GEOJSON_FAMILY_ID},
                headers=_operator_headers(),
            )
    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "not_available"
    assert body["preview_payload"] is None


def test_responses_pass_global_redaction_and_expose_no_public_surface() -> None:
    with TemporaryDirectory() as temp_dir:
        settings = _settings(Path(temp_dir), enabled=True)
        _upgrade_database(settings)
        _write_artifacts(settings)
        with TestClient(create_app(settings), raise_server_exceptions=False) as client:
            allowed = client.get(
                _PATH,
                params={"artifact_family": PHASE_D1_GEOJSON_FAMILY_ID},
                headers=_operator_headers(),
            )
            denied = client.get(
                _PATH,
                params={"artifact_family": PHASE_D1_GEOJSON_FAMILY_ID},
                headers=_operator_headers(authenticated=False),
            )
    # The global verify-redacted middleware would return 500 on a redaction leak.
    assert allowed.status_code == 200
    assert denied.status_code == 403
    _assert_no_public_surface(allowed.text, settings)
    _assert_no_public_surface(denied.text, settings)


def _assert_no_public_surface(text: str, settings: Settings) -> None:
    lowered = text.lower()
    assert "http://" not in lowered
    assert "https://" not in lowered
    assert "/artifacts/" not in lowered
    assert "download_url" not in lowered
    assert "/download/" not in lowered
    assert str(settings.data_dir).lower() not in lowered
    assert "sha256" not in lowered
