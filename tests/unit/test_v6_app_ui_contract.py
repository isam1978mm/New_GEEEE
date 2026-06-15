from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_v6_package_frontend_api_targets_private_operator_routes() -> None:
    source = _read("frontend-v2/src/app/api/v6PackageFlow.ts")

    assert "/operator/v6/package/generate" in source
    assert "/operator/v6/package/review" in source
    assert "/operator/v6/package/download" in source
    assert "Authorization" in source
    assert "categoryCounts" in source
    assert "payloadCount" in source


def test_request_package_panel_has_generate_review_and_retrieve_actions() -> None:
    source = _read("frontend-v2/src/app/components/V6PrivatePackagePanel.tsx")

    assert "Paid Imagery Request Package" in source
    assert "Generate request package" in source
    assert "Review package metadata" in source
    assert "Retrieve package ZIP" in source
    assert "metadata only" in source
    assert "V6 real package flow" not in source
    assert "spatial payloads" in source


def test_operator_private_overlay_section_mounts_v6_package_panel() -> None:
    source = _read("frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx")

    assert "V6PrivatePackagePanel" in source
    assert "operatorAccessToken={resolvedOperatorAccessToken}" in source


def test_v6_package_frontend_files_avoid_public_raw_payload_terms() -> None:
    combined = "\n".join(
        [
            _read("frontend-v2/src/app/api/v6PackageFlow.ts"),
            _read("frontend-v2/src/app/components/V6PrivatePackagePanel.tsx"),
        ]
    ).casefold()

    assert "preview_" + "payload" not in combined
    assert "feature" + "collection" not in combined
    assert "geo" + "json" not in combined
    assert "sha" + "256" not in combined
