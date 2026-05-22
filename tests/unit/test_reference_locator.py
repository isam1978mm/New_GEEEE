from __future__ import annotations

import json

from app.db.models.enums import ArtifactClass
from app.services.reference_locator import (
    REFERENCE_LOCATOR_REPORT_NAME,
    ReferenceLocatorResult,
    ReferenceMatch,
    build_reference_locator_inventory_artifact,
    build_reference_locator_public_summary,
    locate_reference_files,
    write_reference_locator_inventory_report,
)


def test_locate_reference_files_skips_secret_folders_and_matches_safe_roots(tmp_path) -> None:
    safe_root = tmp_path / "refs"
    safe_root.mkdir()
    (safe_root / "reference_manifest.json").write_text("{}", encoding="utf-8")
    (safe_root / "nested").mkdir()
    (safe_root / "nested" / "notes.txt").write_text("ignore", encoding="utf-8")
    (safe_root / "secrets").mkdir()
    (safe_root / "secrets" / "reference_manifest.json").write_text("secret", encoding="utf-8")

    secret_root = tmp_path / "private"
    secret_root.mkdir()
    (secret_root / "reference_manifest.json").write_text("hidden", encoding="utf-8")

    result = locate_reference_files(
        [safe_root, secret_root],
        ["reference_manifest.json"],
    )

    assert len(result.matches) == 1
    assert result.matches[0].search_root == safe_root.resolve().as_posix()
    assert result.matches[0].relative_path == "reference_manifest.json"
    assert secret_root.resolve().as_posix() in result.skipped_secret_roots
    assert (safe_root / "secrets").resolve().as_posix() in result.skipped_secret_directories


def test_reference_locator_public_summary_omits_raw_paths(tmp_path) -> None:
    root_path = (tmp_path / "refs").resolve()
    result = ReferenceLocatorResult(
        requested_names=["reference_manifest.json"],
        searched_roots=[root_path.as_posix()],
        matches=[
            ReferenceMatch(
                requested_name="reference_manifest.json",
                filename="reference_manifest.json",
                search_root=root_path.as_posix(),
                relative_path="nested/reference_manifest.json",
            )
        ],
        skipped_secret_roots=[(tmp_path / "private").resolve().as_posix()],
        skipped_secret_directories=[(tmp_path / "refs" / "secrets").resolve().as_posix()],
        missing_roots=[(tmp_path / "missing").resolve().as_posix()],
    )

    summary = build_reference_locator_public_summary(result)
    serialized = json.dumps(summary, sort_keys=True)

    assert "search_root" not in summary
    assert "relative_path" not in summary
    assert root_path.as_posix() not in serialized
    assert (tmp_path / "private").resolve().as_posix() not in serialized


def test_reference_locator_inventory_report_is_filesystem_only(tmp_path) -> None:
    root_path = (tmp_path / "refs").resolve()
    result = ReferenceLocatorResult(
        requested_names=["reference_manifest.json"],
        searched_roots=[root_path.as_posix()],
        matches=[
            ReferenceMatch(
                requested_name="reference_manifest.json",
                filename="reference_manifest.json",
                search_root=root_path.as_posix(),
                relative_path="reference_manifest.json",
            )
        ],
        skipped_secret_roots=[],
        skipped_secret_directories=[],
        missing_roots=[],
    )

    report_path = write_reference_locator_inventory_report(tmp_path, result)
    artifact = build_reference_locator_inventory_artifact(tmp_path, report_path)
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert report_path == tmp_path / "full_job" / "reference" / REFERENCE_LOCATOR_REPORT_NAME
    assert payload["matches"][0]["relative_path"] == "reference_manifest.json"
    assert payload["public_summary"]["match_count"] == 1
    assert artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY
    assert artifact.http_servable is False
    assert artifact.relative_path == f"full_job/reference/{REFERENCE_LOCATOR_REPORT_NAME}"
