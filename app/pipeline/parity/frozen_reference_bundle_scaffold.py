from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping

from app.pipeline.parity import resolve_run_output_path
from app.services.redaction import verify_redacted


D1_FROZEN_REFERENCE_BUNDLE_SCAFFOLD_SCHEMA_VERSION = (
    "d1_frozen_reference_bundle_scaffold_v1"
)
D1_FROZEN_REFERENCE_BUNDLE_REPORT_RELATIVE_PATH = (
    "manifests/d1_frozen_reference_bundle_scaffold.json"
)
FROZEN_REFERENCE_BUNDLE_MANIFEST_SCHEMA_VERSION = (
    "frozen_notebook_reference_bundle_v1"
)

EXPECTED_FROZEN_REFERENCE_FAMILY_IDS = (
    "report_640",
    "secret_layers",
    "dem_curvature",
    "sar_asc_desc",
    "s1_filtered_stack",
    "pan_stack",
    "pan_components",
    "hypercube_res25",
    "semantic_rasters",
    "private_map_artifacts",
    "phase_c_semantic_feature_writers",
    "phase_d_private_geojson_writer",
    "phase_d2_private_kmz_writer",
    "phase_d3_private_heatmap_json_writer",
)

REQUIRED_FROZEN_REFERENCE_MANIFEST_FIELDS = (
    "bundle_id",
    "schema_version",
    "created_at",
    "created_by",
    "source_notebook_name",
    "source_notebook_version",
    "source_notebook_commit_or_hash",
    "source_run_id",
    "source_grid_id",
    "source_roi_id_redacted",
    "collection_method",
    "collection_environment",
    "artifact_class",
    "filesystem_only",
    "http_servable",
    "frontend_visible",
    "downloadable_via_api",
    "redaction_policy",
    "families",
    "family_inventory",
    "expected_artifact_counts",
    "hashes_available",
    "tolerance_policy_ref",
    "notes",
)

ALLOWED_D1_BUNDLE_STATUSES = (
    "scaffold_defined",
    "not_collected",
    "invalid_manifest",
    "invalid_storage_policy",
    "ready_for_operator_collection",
    "ready_for_later_verifier_run",
)

_ALLOWED_ARTIFACT_CLASSES = ("LOCAL_SENSITIVE", "FILESYSTEM_ONLY")
_REPO_ROOT = Path(__file__).resolve().parents[3]


def get_frozen_reference_bundle_scaffold() -> dict[str, Any]:
    layout = [
        "data/notebook_references/<bundle_id>/manifest.json",
        "data/notebook_references/<bundle_id>/references/",
        *(
            f"data/notebook_references/<bundle_id>/references/{family_id}/"
            for family_id in EXPECTED_FROZEN_REFERENCE_FAMILY_IDS
        ),
        *(
            f"references/{family_id}/"
            for family_id in EXPECTED_FROZEN_REFERENCE_FAMILY_IDS
        ),
    ]
    return {
        "scaffold_id": "d1_frozen_reference_bundle_scaffold",
        "bundle_root_template": "data/notebook_references/<bundle_id>",
        "manifest_name": "manifest.json",
        "references_dir_name": "references",
        "expected_bundle_layout": layout,
        "required_manifest_fields": list(REQUIRED_FROZEN_REFERENCE_MANIFEST_FIELDS),
        "expected_family_ids": list(EXPECTED_FROZEN_REFERENCE_FAMILY_IDS),
        "storage_policy": _storage_policy(),
        "redaction_policy": {
            "public_summary_excludes_exact_coordinates": True,
            "public_summary_excludes_raw_shapes": True,
            "public_summary_excludes_filesystem_refs": True,
            "public_summary_excludes_private_digests": True,
            "public_summary_excludes_artifact_payloads": True,
        },
        "collection_checklist": _collection_checklist(),
        "handoff_to_verifiers": _handoff_to_verifiers(),
    }


def validate_frozen_reference_bundle_manifest(
    bundle_root: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(bundle_root)
    if not _bundle_root_storage_allowed(root, repo_root=repo_root):
        return _validation_result(
            status="invalid_storage_policy",
            blockers=("bundle_root_must_be_outside_git_or_pytest_tmp",),
        )

    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return _validation_result(
            status="not_collected",
            blockers=("manifest_not_collected",),
        )

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _validation_result(
            status="invalid_manifest",
            blockers=("manifest_unreadable",),
        )
    if not isinstance(payload, Mapping):
        return _validation_result(
            status="invalid_manifest",
            blockers=("manifest_not_object",),
        )

    missing_fields = [
        field for field in REQUIRED_FROZEN_REFERENCE_MANIFEST_FIELDS if field not in payload
    ]
    if missing_fields:
        return _validation_result(
            status="invalid_manifest",
            blockers=("manifest_missing_required_fields",),
            missing_manifest_fields=missing_fields,
        )
    if payload.get("schema_version") != FROZEN_REFERENCE_BUNDLE_MANIFEST_SCHEMA_VERSION:
        return _validation_result(
            status="invalid_manifest",
            blockers=("manifest_schema_version_unsupported",),
        )
    storage_blockers = _storage_policy_blockers(payload)
    if storage_blockers:
        return _validation_result(
            status="invalid_storage_policy",
            blockers=tuple(storage_blockers),
        )

    families = payload.get("families")
    family_inventory = payload.get("family_inventory")
    expected_counts = payload.get("expected_artifact_counts")
    if not isinstance(families, list) or set(families) != set(
        EXPECTED_FROZEN_REFERENCE_FAMILY_IDS
    ):
        return _validation_result(
            status="invalid_manifest",
            blockers=("manifest_family_list_invalid",),
        )
    if not isinstance(family_inventory, Mapping) or not isinstance(
        expected_counts, Mapping
    ):
        return _validation_result(
            status="invalid_manifest",
            blockers=("manifest_family_inventory_invalid",),
        )

    missing_reference_families = []
    for family_id in EXPECTED_FROZEN_REFERENCE_FAMILY_IDS:
        inventory = family_inventory.get(family_id)
        expected_count = expected_counts.get(family_id)
        if not isinstance(inventory, list) or not isinstance(expected_count, int):
            return _validation_result(
                status="invalid_manifest",
                blockers=("manifest_family_inventory_invalid",),
            )
        if expected_count > len(inventory):
            missing_reference_families.append(family_id)

    if missing_reference_families:
        return _validation_result(
            status="not_collected",
            blockers=("missing_references",),
            missing_reference_families=missing_reference_families,
        )

    return _validation_result(
        status="ready_for_later_verifier_run",
        blockers=(),
    )


def write_frozen_reference_bundle_scaffold_report(
    *,
    run_dir: str | Path,
    run_id: str,
    bundle_status: str = "ready_for_operator_collection",
    report_relative_path: str | Path = D1_FROZEN_REFERENCE_BUNDLE_REPORT_RELATIVE_PATH,
) -> Path:
    if bundle_status not in ALLOWED_D1_BUNDLE_STATUSES:
        raise ValueError(f"unsupported D1 bundle status: {bundle_status}")
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    scaffold = get_frozen_reference_bundle_scaffold()
    payload: dict[str, Any] = {
        "schema_version": D1_FROZEN_REFERENCE_BUNDLE_SCAFFOLD_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "scaffold_id": scaffold["scaffold_id"],
        "expected_bundle_layout": scaffold["expected_bundle_layout"],
        "required_manifest_fields": scaffold["required_manifest_fields"],
        "expected_family_ids": scaffold["expected_family_ids"],
        "storage_policy": scaffold["storage_policy"],
        "redaction_policy": scaffold["redaction_policy"],
        "collection_checklist": scaffold["collection_checklist"],
        "handoff_to_verifiers": scaffold["handoff_to_verifiers"],
        "bundle_status": bundle_status,
        "notebook_value_parity_verified": False,
        "runtime_output_verified": False,
        "collection_plan_only": True,
        "real_references_collected": False,
        "artifact_generation": False,
        "earth_engine_calls_added": False,
        "public_exposure_changes": False,
        "notes": (
            "D1 defines the private frozen-reference bundle scaffold and operator "
            "collection checklist only. Missing references are not success."
        ),
    }
    verify_redacted(payload)
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _storage_policy() -> dict[str, Any]:
    return {
        "allowed_artifact_classes": list(_ALLOWED_ARTIFACT_CLASSES),
        "filesystem_only_required": True,
        "http_servable_required": False,
        "frontend_visible_required": False,
        "downloadable_via_api_required": False,
        "bundle_root_must_be_outside_git": True,
        "pytest_tmp_allowed_for_tests": True,
    }


def _collection_checklist() -> list[str]:
    return [
        "choose_private_bundle_root_outside_git",
        "capture_manifest_with_required_fields",
        "create_references_subfolders_for_expected_families",
        "record_per_family_artifact_inventory",
        "classify_bundle_local_sensitive_or_filesystem_only",
        "keep_public_summaries_redacted",
        "run_phase_e_e3_e4_verifiers_later",
    ]


def _handoff_to_verifiers() -> dict[str, list[str]]:
    return {
        "phase_e_private_frozen_reference_verifier": [
            "report_640",
            "secret_layers",
            "dem_curvature",
            "sar_asc_desc",
            "s1_filtered_stack",
            "pan_stack",
            "pan_components",
            "hypercube_res25",
            "semantic_rasters",
            "private_map_artifacts",
            "phase_c_semantic_feature_writers",
            "phase_d_private_geojson_writer",
        ],
        "phase_e3_semantic_feature_comparator": [
            "phase_c_semantic_feature_writers",
        ],
        "phase_e4_private_map_artifact_comparator": [
            "phase_d_private_geojson_writer",
            "phase_d2_private_kmz_writer",
            "phase_d3_private_heatmap_json_writer",
        ],
    }


def _validation_result(
    *,
    status: str,
    blockers: tuple[str, ...],
    missing_manifest_fields: list[str] | None = None,
    missing_reference_families: list[str] | None = None,
) -> dict[str, Any]:
    if status not in ALLOWED_D1_BUNDLE_STATUSES:
        raise ValueError(f"unsupported D1 validation status: {status}")
    return {
        "status": status,
        "blockers": list(blockers),
        "missing_manifest_fields": missing_manifest_fields or [],
        "missing_reference_families": missing_reference_families or [],
        "notebook_value_parity_verified": False,
        "runtime_output_verified": False,
        "real_references_collected": False,
        "collection_plan_only": True,
    }


def _bundle_root_storage_allowed(
    bundle_root: Path,
    *,
    repo_root: str | Path | None,
) -> bool:
    resolved = bundle_root.resolve()
    if _is_pytest_tmp_path(resolved):
        return True
    repo = Path(repo_root).resolve() if repo_root is not None else _REPO_ROOT
    try:
        resolved.relative_to(repo)
    except ValueError:
        return True
    return False


def _is_pytest_tmp_path(path: Path) -> bool:
    lowered = str(path).lower()
    if "pytest" in lowered:
        return True
    try:
        path.relative_to(Path(tempfile.gettempdir()).resolve())
        return True
    except ValueError:
        return False


def _storage_policy_blockers(payload: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if payload.get("artifact_class") not in _ALLOWED_ARTIFACT_CLASSES:
        blockers.append("artifact_class_must_be_local_sensitive_or_filesystem_only")
    if payload.get("filesystem_only") is not True:
        blockers.append("filesystem_only_must_be_true")
    if payload.get("http_servable") is not False:
        blockers.append("http_servable_must_be_false")
    if payload.get("frontend_visible") is not False:
        blockers.append("frontend_visible_must_be_false")
    if payload.get("downloadable_via_api") is not False:
        blockers.append("downloadable_via_api_must_be_false")
    return blockers
