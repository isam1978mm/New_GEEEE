from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from app.pipeline.parity import resolve_run_output_path
from app.pipeline.parity.end_to_end_harness import (
    EndToEndFamilyResult,
    run_end_to_end_notebook_parity_harness,
)


PHASE_E_FROZEN_REFERENCE_VERIFIER_SCHEMA_VERSION = (
    "phase_e_private_frozen_reference_verifier_v1"
)
PHASE_E_FROZEN_REFERENCE_VERIFIER_REPORT_RELATIVE_PATH = (
    "manifests/private_frozen_reference_verifier_report.json"
)
FROZEN_REFERENCE_BUNDLE_SCHEMA_VERSION = "frozen_notebook_reference_bundle_v1"

REQUIRED_PHASE_E_FAMILIES = {
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
}

_HARNESS_DELEGATED_FAMILIES = {
    "report_640",
    "secret_layers",
    "dem_curvature",
    "sar_asc_desc",
    "s1_filtered_stack",
    "pan_stack",
    "pan_components",
    "hypercube_res25",
}

_INVENTORY_ONLY_FAMILIES = {
    "semantic_rasters",
    "private_map_artifacts",
}

_PHASE_C_OUTPUTS = (
    "AI_BEH_VegRoot_REL_ND_DOM_lin_640.npy",
    "AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.npy",
    "AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.npy",
)
_PHASE_D_OUTPUTS = ("private_features.geojson",)


@dataclass(frozen=True)
class FrozenReferenceBundleValidation:
    status: str
    bundle_id: str
    manifest_path: Path | None
    files_by_family: dict[str, tuple[str, ...]]
    notes: str


@dataclass(frozen=True)
class PrivateFrozenReferenceVerifierResult:
    report_path: Path
    reference_bundle_status: str
    overall_status: str
    families: tuple[EndToEndFamilyResult, ...]
    runtime_output_verified: bool
    notebook_value_parity_verified: bool


def validate_frozen_reference_bundle(
    reference_bundle_dir: str | Path,
) -> FrozenReferenceBundleValidation:
    """Validate the Phase E frozen notebook reference-bundle manifest."""

    bundle_root = Path(reference_bundle_dir)
    if not bundle_root.is_dir():
        return FrozenReferenceBundleValidation(
            status="reference_missing",
            bundle_id="",
            manifest_path=None,
            files_by_family={},
            notes="Frozen notebook reference bundle directory is missing.",
        )

    manifest_path = bundle_root / "manifest.json"
    if not manifest_path.is_file():
        return FrozenReferenceBundleValidation(
            status="reference_missing",
            bundle_id="",
            manifest_path=manifest_path,
            files_by_family={},
            notes="Frozen notebook reference bundle manifest.json is missing.",
        )

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return FrozenReferenceBundleValidation(
            status="error",
            bundle_id="",
            manifest_path=manifest_path,
            files_by_family={},
            notes=f"Frozen notebook reference bundle manifest could not be parsed: {exc}",
        )
    if not isinstance(payload, Mapping):
        return FrozenReferenceBundleValidation(
            status="error",
            bundle_id="",
            manifest_path=manifest_path,
            files_by_family={},
            notes="Frozen notebook reference bundle manifest must be a JSON object.",
        )

    schema_version = payload.get("schema_version")
    bundle_id = payload.get("bundle_id")
    files = payload.get("files")
    if schema_version != FROZEN_REFERENCE_BUNDLE_SCHEMA_VERSION:
        return FrozenReferenceBundleValidation(
            status="error",
            bundle_id=str(bundle_id or ""),
            manifest_path=manifest_path,
            files_by_family={},
            notes="Frozen notebook reference bundle manifest schema_version is unsupported.",
        )
    if not isinstance(bundle_id, str) or not bundle_id.strip():
        return FrozenReferenceBundleValidation(
            status="error",
            bundle_id="",
            manifest_path=manifest_path,
            files_by_family={},
            notes="Frozen notebook reference bundle manifest bundle_id is missing.",
        )
    if not isinstance(files, Mapping):
        return FrozenReferenceBundleValidation(
            status="error",
            bundle_id=bundle_id,
            manifest_path=manifest_path,
            files_by_family={},
            notes="Frozen notebook reference bundle manifest files field must be an object.",
        )

    files_by_family: dict[str, tuple[str, ...]] = {}
    for family_id, family_files in files.items():
        if not isinstance(family_id, str) or not family_id:
            return FrozenReferenceBundleValidation(
                status="error",
                bundle_id=bundle_id,
                manifest_path=manifest_path,
                files_by_family={},
                notes="Frozen notebook reference bundle family ids must be non-empty strings.",
            )
        if not isinstance(family_files, list) or not all(
            isinstance(item, str) for item in family_files
        ):
            return FrozenReferenceBundleValidation(
                status="error",
                bundle_id=bundle_id,
                manifest_path=manifest_path,
                files_by_family={},
                notes=f"Frozen notebook reference files for {family_id} must be a list of strings.",
            )
        files_by_family[family_id] = tuple(family_files)

    return FrozenReferenceBundleValidation(
        status="present",
        bundle_id=bundle_id,
        manifest_path=manifest_path,
        files_by_family=files_by_family,
        notes="Frozen notebook reference bundle manifest is readable.",
    )


def run_private_frozen_reference_verifier(
    *,
    app_output_dir: str | Path,
    reference_bundle_dir: str | Path,
    run_dir: str | Path,
    run_id: str,
    selected_families: Iterable[str] | None = None,
    tolerances: Mapping[str, Mapping[str, float]] | None = None,
    report_relative_path: str | Path = PHASE_E_FROZEN_REFERENCE_VERIFIER_REPORT_RELATIVE_PATH,
) -> PrivateFrozenReferenceVerifierResult:
    """Validate a frozen bundle and run private read-only parity checks."""

    app_root = Path(app_output_dir)
    bundle_root = Path(reference_bundle_dir)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    selected = tuple(selected_families or sorted(REQUIRED_PHASE_E_FAMILIES))
    unknown = sorted(set(selected) - REQUIRED_PHASE_E_FAMILIES)
    if unknown:
        raise ValueError(f"unsupported Phase E families: {', '.join(unknown)}")

    validation = validate_frozen_reference_bundle(bundle_root)
    if validation.status != "present":
        family_results = tuple(
            _blocked_family_result(
                family_id,
                status=validation.status,
                reference_status="missing" if validation.status == "reference_missing" else "not_checked",
                app_output_status="present" if app_root.is_dir() else "missing",
                blocker=validation.notes,
                next_action="Provide a readable frozen notebook reference bundle before running private parity verification.",
            )
            for family_id in selected
        )
    elif not app_root.is_dir():
        family_results = tuple(
            _blocked_family_result(
                family_id,
                status="app_output_missing",
                reference_status="present",
                app_output_status="missing",
                blocker="App output directory is missing.",
                next_action="Provide an app output directory before running private parity verification.",
            )
            for family_id in selected
        )
    else:
        family_results = tuple(
            _run_family(
                family_id,
                app_output_dir=app_root,
                reference_bundle_dir=bundle_root,
                validation=validation,
                run_dir=Path(run_dir),
                run_id=run_id,
                tolerances=(tolerances or {}).get(family_id, {}),
            )
            for family_id in selected
        )

    overall_status = _overall_status(family_results)
    runtime_output_verified = _overall_runtime_verified(family_results)
    notebook_value_parity_verified = overall_status == "passed"

    payload = {
        "schema_version": PHASE_E_FROZEN_REFERENCE_VERIFIER_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "app_output_dir": str(app_root),
        "reference_bundle_dir": str(bundle_root),
        "reference_bundle_status": validation.status,
        "selected_families": list(selected),
        "families": [family.to_dict() for family in family_results],
        "counts_by_family_status": _counts_by_status(family_results),
        "overall_status": overall_status,
        "runtime_output_verified": runtime_output_verified,
        "notebook_value_parity_verified": notebook_value_parity_verified,
        "phase_e_runtime_changes": False,
        "public_exposure_changes": False,
        "artifact_generation": False,
        "earth_engine_calls_added": False,
        "notes": (
            "Phase E validates private frozen notebook reference bundles and runs read-only "
            "parity checks where verifier-backed families exist. It does not generate app "
            "outputs or expose private artifacts."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return PrivateFrozenReferenceVerifierResult(
        report_path=report_path,
        reference_bundle_status=validation.status,
        overall_status=overall_status,
        families=family_results,
        runtime_output_verified=runtime_output_verified,
        notebook_value_parity_verified=notebook_value_parity_verified,
    )


def _run_family(
    family_id: str,
    *,
    app_output_dir: Path,
    reference_bundle_dir: Path,
    validation: FrozenReferenceBundleValidation,
    run_dir: Path,
    run_id: str,
    tolerances: Mapping[str, float],
) -> EndToEndFamilyResult:
    if family_id in _INVENTORY_ONLY_FAMILIES:
        return _inventory_family_result(family_id)
    if family_id == "phase_c_semantic_feature_writers":
        return _presence_family_result(
            family_id=family_id,
            contract_doc="docs/IMPLEMENTATION_PHASE_C_DEFENSIBLE_RASTER_FEATURE_WRITERS.md",
            module_used="app.pipeline.parity.semantic_feature_writers",
            expected_reference_artifacts=validation.files_by_family.get(
                family_id,
                _PHASE_C_OUTPUTS,
            ),
            app_output_dir=app_output_dir,
            reference_family_dir=reference_bundle_dir / "references" / family_id,
        )
    if family_id == "phase_d_private_geojson_writer":
        return _presence_family_result(
            family_id=family_id,
            contract_doc="docs/IMPLEMENTATION_PHASE_D_PRIVATE_MAP_ARTIFACT_WRITERS.md",
            module_used="app.pipeline.parity.private_map_artifact_writers",
            expected_reference_artifacts=validation.files_by_family.get(
                family_id,
                _PHASE_D_OUTPUTS,
            ),
            app_output_dir=app_output_dir,
            reference_family_dir=reference_bundle_dir / "references" / family_id,
        )
    if family_id in _HARNESS_DELEGATED_FAMILIES:
        reference_family_dir = reference_bundle_dir / "references" / family_id
        if not reference_family_dir.is_dir():
            return _blocked_family_result(
                family_id,
                status="reference_missing",
                reference_status="missing",
                app_output_status="present",
                blocker=f"Frozen reference family directory is missing for {family_id}.",
                next_action="Populate references/<family_id>/ before running this verifier-backed family.",
            )
        result = run_end_to_end_notebook_parity_harness(
            app_output_dir=app_output_dir,
            reference_bundle_dir=reference_family_dir,
            run_dir=run_dir,
            run_id=run_id,
            selected_families=(family_id,),
            tolerances={family_id: dict(tolerances)},
            report_relative_path=Path("manifests") / ".phase_e_tmp" / f"{family_id}.json",
        )
        _cleanup_temporary_report(result.report_path, run_dir)
        return result.families[0]

    return _blocked_family_result(
        family_id,
        status="verifier_not_available",
        reference_status="not_checked",
        app_output_status="not_checked",
        blocker="No Phase E verifier route is available for this family.",
        next_action="Add a source/reference-driven verifier slice before expecting notebook-value parity.",
    )


def _presence_family_result(
    *,
    family_id: str,
    contract_doc: str,
    module_used: str,
    expected_reference_artifacts: Iterable[str],
    app_output_dir: Path,
    reference_family_dir: Path,
) -> EndToEndFamilyResult:
    expected = tuple(expected_reference_artifacts)
    if not expected:
        return _blocked_family_result(
            family_id,
            status="reference_missing",
            reference_status="missing",
            app_output_status="not_checked",
            blocker=f"No expected frozen reference files are listed for {family_id}.",
            next_action="Add file entries to the frozen reference bundle manifest for this family.",
            contract_doc=contract_doc,
            module_used=module_used,
            expected_reference_artifacts=expected,
        )

    reference_presence = [
        (reference_family_dir / relative_path).is_file() for relative_path in expected
    ]
    if not all(reference_presence):
        return _blocked_family_result(
            family_id,
            status="reference_missing",
            reference_status=_presence_to_status(reference_presence),
            app_output_status="not_checked",
            blocker=f"Frozen reference files are missing for {family_id}.",
            next_action="Provide the missing frozen notebook reference files before verification.",
            contract_doc=contract_doc,
            module_used=module_used,
            expected_reference_artifacts=expected,
        )

    app_presence = [_app_file_exists(app_output_dir, relative_path) for relative_path in expected]
    if not all(app_presence):
        return _blocked_family_result(
            family_id,
            status="app_output_missing",
            reference_status="present",
            app_output_status=_presence_to_status(app_presence),
            blocker=f"App output files are missing for {family_id}.",
            next_action="Produce app outputs in a separate implementation/run step before comparing values.",
            contract_doc=contract_doc,
            module_used=module_used,
            expected_reference_artifacts=expected,
        )

    return EndToEndFamilyResult(
        family_id=family_id,
        contract_doc=contract_doc,
        module_used=module_used,
        expected_reference_artifacts=expected,
        app_output_status="present",
        reference_status="present",
        runtime_output_verified=True,
        notebook_value_parity_verified=False,
        comparison_status="verifier_not_available",
        status="verifier_not_available",
        blocker="Reference and app files are present, but no value comparator is implemented for this Phase E family.",
        recommended_next_action="Add a dedicated read-only verifier before notebook-value parity can pass.",
        notes="Phase E records presence only and keeps notebook-value parity false.",
    )


def _inventory_family_result(family_id: str) -> EndToEndFamilyResult:
    if family_id == "semantic_rasters":
        contract_doc = "docs/SEMANTIC_RASTER_RECOVERY_CONTRACT.md"
        module_used = "app.pipeline.parity.semantic_raster_recovery"
        expected = ("frozen notebook semantic raster outputs",)
    else:
        contract_doc = "docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md"
        module_used = "app.pipeline.parity.private_map_artifact_inventory"
        expected = ("frozen notebook private coordinate/map artifact bundle",)
    return EndToEndFamilyResult(
        family_id=family_id,
        contract_doc=contract_doc,
        module_used=module_used,
        expected_reference_artifacts=expected,
        app_output_status="not_checked",
        reference_status="not_checked",
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status="inventory_only",
        status="inventory_only",
        blocker="This family is inventory-only in Phase E.",
        recommended_next_action="Add a dedicated verifier slice before treating this family as notebook-value comparable.",
        notes="Inventory-only families do not affect notebook-value parity success.",
    )


def _blocked_family_result(
    family_id: str,
    *,
    status: str,
    reference_status: str,
    app_output_status: str,
    blocker: str,
    next_action: str,
    contract_doc: str = "docs/IMPLEMENTATION_PHASE_E_PRIVATE_PARITY_VERIFIER.md",
    module_used: str = "app.pipeline.parity.frozen_reference_verifier",
    expected_reference_artifacts: Iterable[str] = (),
) -> EndToEndFamilyResult:
    return EndToEndFamilyResult(
        family_id=family_id,
        contract_doc=contract_doc,
        module_used=module_used,
        expected_reference_artifacts=tuple(expected_reference_artifacts),
        app_output_status=app_output_status,
        reference_status=reference_status,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        comparison_status=status,
        status=status,
        blocker=blocker,
        recommended_next_action=next_action,
        notes="Phase E treats missing or unavailable comparison inputs as not passing.",
    )


def _app_file_exists(app_output_dir: Path, relative_path: str) -> bool:
    direct = app_output_dir / relative_path
    if direct.is_file():
        return True
    name = Path(relative_path).name
    return any(path.name == name for path in app_output_dir.rglob("*") if path.is_file())


def _presence_to_status(values: Iterable[bool]) -> str:
    values_tuple = tuple(values)
    if not values_tuple:
        return "not_checked"
    if all(values_tuple):
        return "present"
    if any(values_tuple):
        return "mixed"
    return "missing"


def _overall_status(families: Iterable[EndToEndFamilyResult]) -> str:
    statuses = [family.status for family in families]
    if not statuses:
        return "inventory_only"
    if any(status == "error" for status in statuses):
        return "error"
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status == "comparison_unavailable" for status in statuses):
        return "comparison_unavailable"
    if any(
        status
        in {
            "reference_missing",
            "app_output_missing",
            "incomplete",
            "verifier_not_available",
        }
        for status in statuses
    ):
        return "incomplete"
    if all(status in {"inventory_only", "design_only", "decision_only"} for status in statuses):
        return "inventory_only"
    if any(status == "passed" for status in statuses) and all(
        status in {"passed", "inventory_only", "design_only", "decision_only"}
        for status in statuses
    ):
        return "passed"
    return "incomplete"


def _overall_runtime_verified(families: Iterable[EndToEndFamilyResult]) -> bool:
    verifier_families = [
        family
        for family in families
        if family.status
        not in {
            "inventory_only",
            "design_only",
            "decision_only",
            "verifier_not_available",
            "skipped_by_request",
        }
    ]
    if not verifier_families:
        return False
    return all(family.runtime_output_verified for family in verifier_families)


def _counts_by_status(families: Iterable[EndToEndFamilyResult]) -> dict[str, int]:
    statuses = {
        "passed",
        "failed",
        "incomplete",
        "reference_missing",
        "app_output_missing",
        "comparison_unavailable",
        "inventory_only",
        "design_only",
        "decision_only",
        "verifier_not_available",
        "skipped_by_request",
        "error",
    }
    counts = {status: 0 for status in sorted(statuses)}
    for family in families:
        counts[family.status] += 1
    return counts


def _cleanup_temporary_report(report_path: Path, run_dir: Path) -> None:
    resolved_run_dir = Path(run_dir).resolve()
    resolved_report = report_path.resolve()
    resolved_report.relative_to(resolved_run_dir)
    if report_path.exists():
        report_path.unlink()
    parent = report_path.parent
    manifests_root = resolved_run_dir / "manifests"
    while parent not in {resolved_run_dir, manifests_root} and parent.exists():
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent
