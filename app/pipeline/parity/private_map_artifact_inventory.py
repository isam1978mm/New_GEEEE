from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Iterable

from app.pipeline.parity import resolve_run_output_path


PHASE_6_PRIVATE_MAP_ARTIFACT_SCHEMA_VERSION = (
    "phase_6_private_map_artifact_inventory_v1"
)
PHASE_6_PRIVATE_MAP_ARTIFACT_REPORT_RELATIVE_PATH = (
    "manifests/phase_6_private_map_artifact_inventory.json"
)

ALLOWED_CATEGORIES = {
    "kmz_outputs",
    "geojson_outputs",
    "heatmap_outputs",
    "visual_map_outputs",
    "coordinate_bearing_filesystem_artifacts",
    "redaction_and_serving_policy",
}

ALLOWED_SOURCE_STATUSES = {
    "exact_source_found",
    "partial_source_found",
    "no_source_found",
    "existing_app_equivalent_found",
    "unknown_needs_reference",
}

ALLOWED_PARITY_STATUSES = {
    "covered_by_existing_contract",
    "inventory_only",
    "verifier_needed",
    "reference_needed",
    "source_recovery_needed",
    "implementation_later",
    "blocked",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "no_action_needed_existing_contract",
    "requires_verifier_contract",
    "requires_reference_output",
    "requires_source_reconstruction",
    "requires_private_writer_contract",
    "requires_inventory_reconciliation",
    "implementation_deferred",
}

ALLOWED_ARTIFACT_CLASSES = {
    "LOCAL_SENSITIVE",
    "PRIVATE_COORDINATE_ARTIFACT",
}

_COMMON_REQUIRED_METADATA = (
    "artifact class and private filesystem-only policy",
    "run-relative path mapping",
    "coordinate, geometry, bounds, and CRS or transform presence",
    "notebook reference filename or artifact pattern",
    "source cell or app stage evidence",
    "redaction boundary for any public DTO references",
)


@dataclass(frozen=True)
class PrivateMapArtifactInventoryItem:
    id: str
    category: str
    notebook_artifact_or_pattern: str
    current_app_artifact_or_pattern: str
    source_status: str
    current_app_status: str
    parity_status: str
    contains_coordinates: bool
    contains_geometry: bool
    contains_bounds: bool
    contains_crs_or_transform: bool
    expected_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    required_reference_artifacts: tuple[str, ...]
    required_metadata: tuple[str, ...]
    target_mode: str
    classification: str
    artifact_class: str
    filesystem_only: bool
    http_servable: bool
    frontend_visible: bool
    downloadable_via_api: bool
    runtime_output_verified: bool
    notebook_value_parity_verified: bool
    implementation_status: str
    blocker: str
    recommended_next_action: str
    notes: str

    def __post_init__(self) -> None:
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"unsupported category: {self.category}")
        if self.source_status not in ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"unsupported source_status: {self.source_status}")
        if self.parity_status not in ALLOWED_PARITY_STATUSES:
            raise ValueError(f"unsupported parity_status: {self.parity_status}")
        if self.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"unsupported implementation_status: {self.implementation_status}"
            )
        if self.artifact_class not in ALLOWED_ARTIFACT_CLASSES:
            raise ValueError(f"unsupported artifact_class: {self.artifact_class}")
        if self.target_mode == "public_shared":
            raise ValueError("Phase 6 inventory items must not target public_shared")
        if not self.filesystem_only:
            raise ValueError("Phase 6 private map artifacts must remain filesystem_only")
        if self.http_servable:
            raise ValueError("Phase 6 private map artifacts must not be http_servable")
        if self.frontend_visible:
            raise ValueError("Phase 6 private map artifacts must not be frontend_visible")
        if self.downloadable_via_api:
            raise ValueError(
                "Phase 6 private map artifacts must not be downloadable_via_api"
            )
        if self.notebook_value_parity_verified:
            raise ValueError("Phase 6 inventory only; notebook value parity must be false")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_INVENTORY: tuple[PrivateMapArtifactInventoryItem, ...] = (
    PrivateMapArtifactInventoryItem(
        id="phase6_kmz_outputs",
        category="kmz_outputs",
        notebook_artifact_or_pattern=(
            "AI_HEATMAP_CLASSIFICATION.kmz | AI_3D_TARGET_VISUALIZATION.kmz | "
            "AI_TARGETS_ONLY_17M.kmz | AI_TARGETS_3D_ONLY.kmz | "
            "TESLA_V7_2_FIELD_OPERATIONS.kmz | FINAL_TARGETS_FIELD_MAP.kmz | "
            "FINAL_TARGETS_FIELD_NAV_V7_2.kmz"
        ),
        current_app_artifact_or_pattern=(
            "kmz/site_location.kmz | kmz/field_ops_navigation.kmz"
        ),
        source_status="partial_source_found",
        current_app_status=(
            "Location and field-ops stages write private local KMZ artifacts, but notebook "
            "heatmap and target KMZ families are broader than current app outputs."
        ),
        parity_status="reference_needed",
        contains_coordinates=True,
        contains_geometry=True,
        contains_bounds=False,
        contains_crs_or_transform=False,
        expected_inputs=("selected point", "GRID center", "field navigation geometry"),
        expected_outputs=("private KMZ artifacts under run-local output folders",),
        required_reference_artifacts=(
            "frozen notebook KMZ bundle",
            "notebook cell-to-filename mapping for generated KMZ outputs",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity_private",
        classification="private notebook-parity coordinate/map artifact inventory",
        artifact_class="PRIVATE_COORDINATE_ARTIFACT",
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_reference_output",
        blocker="Frozen notebook KMZ references and exact filename mapping are not yet available to this inventory.",
        recommended_next_action="Capture the frozen notebook KMZ bundle before drafting a private KMZ verifier contract.",
        notes=(
            "Existing local KMZ files remain private candidate artifacts only. They are not "
            "treated as notebook-value matches or HTTP-downloadable outputs."
        ),
    ),
    PrivateMapArtifactInventoryItem(
        id="phase6_geojson_outputs",
        category="geojson_outputs",
        notebook_artifact_or_pattern=(
            "SelectedPoint GeoJSON | geojson_features dumps | target and detection GeoJSON "
            "feature collections"
        ),
        current_app_artifact_or_pattern=(
            "full_job/location/site_location.geojson | field_ops_report.json candidate "
            "coordinate payloads"
        ),
        source_status="partial_source_found",
        current_app_status=(
            "Location stage writes a private site_location.geojson; broader notebook GeoJSON "
            "feature dumps need reference naming and payload evidence."
        ),
        parity_status="source_recovery_needed",
        contains_coordinates=True,
        contains_geometry=True,
        contains_bounds=False,
        contains_crs_or_transform=False,
        expected_inputs=("selected point", "target feature collections", "GRID metadata"),
        expected_outputs=("private GeoJSON or JSON feature artifacts",),
        required_reference_artifacts=(
            "frozen notebook GeoJSON feature artifacts",
            "source cell snippets that define expected feature schemas",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity_private",
        classification="private notebook-parity coordinate feature inventory",
        artifact_class="PRIVATE_COORDINATE_ARTIFACT",
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_source_reconstruction",
        blocker="Notebook GeoJSON source references are partial and do not yet lock exact schemas for every output pattern.",
        recommended_next_action="Recover notebook GeoJSON schemas and frozen feature artifacts before any private verifier slice.",
        notes="GeoJSON-like app files are private candidates only and are not listed or served through public API DTOs.",
    ),
    PrivateMapArtifactInventoryItem(
        id="phase6_heatmap_outputs",
        category="heatmap_outputs",
        notebook_artifact_or_pattern=(
            "AI_HEATMAP_CLASSIFICATION.kmz | heatmap classification overlays | regenerated "
            "simplekml heatmap artifacts"
        ),
        current_app_artifact_or_pattern="No dedicated app heatmap map artifact writer in Phase 6 scope.",
        source_status="partial_source_found",
        current_app_status="No live app heatmap export is introduced or required by this Phase 6 inventory.",
        parity_status="implementation_later",
        contains_coordinates=True,
        contains_geometry=True,
        contains_bounds=True,
        contains_crs_or_transform=False,
        expected_inputs=("classifier or probability matrices", "GRID georeferencing", "map overlay thresholds"),
        expected_outputs=("private heatmap KMZ or map overlay artifacts if later implemented",),
        required_reference_artifacts=(
            "frozen notebook heatmap KMZ or overlay artifacts",
            "source evidence for heatmap color, threshold, and geometry policy",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity_private",
        classification="private notebook-parity heatmap artifact inventory",
        artifact_class="PRIVATE_COORDINATE_ARTIFACT",
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_private_writer_contract",
        blocker="Notebook heatmap artifacts depend on private coordinate overlays and later implementation policy.",
        recommended_next_action="Define a later private heatmap writer and verifier contract only after source and reference artifacts are locked.",
        notes="Phase 6 does not create heatmaps, map overlays, tiles, or frontend previews.",
    ),
    PrivateMapArtifactInventoryItem(
        id="phase6_visual_map_outputs",
        category="visual_map_outputs",
        notebook_artifact_or_pattern=(
            "visual_inspection_map.html | geemap.Map/folium visual layers | live target "
            "marker and buffer overlays"
        ),
        current_app_artifact_or_pattern="No app public visual map output or frontend preview for notebook maps.",
        source_status="partial_source_found",
        current_app_status="The app does not expose notebook visual map artifacts in Phase 6.",
        parity_status="implementation_later",
        contains_coordinates=True,
        contains_geometry=True,
        contains_bounds=True,
        contains_crs_or_transform=False,
        expected_inputs=("selected point", "GRID bounds", "target marker features", "map layer settings"),
        expected_outputs=("private visual map artifact if later approved",),
        required_reference_artifacts=(
            "frozen notebook visual map artifact or rendered map evidence",
            "source evidence for layers, markers, buffers, and basemap policy",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity_private",
        classification="private notebook-parity visual map inventory",
        artifact_class="PRIVATE_COORDINATE_ARTIFACT",
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_private_writer_contract",
        blocker="Notebook visual map outputs are interactive/private and are not suitable for public exposure by default.",
        recommended_next_action="Keep visual map parity as a later private artifact contract if frozen references and user-approved policy exist.",
        notes="No map tiles, visual overlays, or frontend map previews are added by this inventory.",
    ),
    PrivateMapArtifactInventoryItem(
        id="phase6_coordinate_bearing_filesystem_artifacts",
        category="coordinate_bearing_filesystem_artifacts",
        notebook_artifact_or_pattern=(
            "CSV/JSON/KML/KMZ field navigation, GPS comparison, focus-map, and target "
            "coordinate artifacts"
        ),
        current_app_artifact_or_pattern=(
            "full_job/gps/gps_point_comparison.json | full_job/gps/gps_point_comparison.csv | "
            "full_job/field_ops/field_ops_report.json | full_job/field_ops/field_ops_brief.txt | "
            "focus_zone_summary.json"
        ),
        source_status="existing_app_equivalent_found",
        current_app_status=(
            "Several app stages write private coordinate-bearing filesystem artifacts, but "
            "Phase 6 does not make them notebook parity outputs or public resources."
        ),
        parity_status="inventory_only",
        contains_coordinates=True,
        contains_geometry=False,
        contains_bounds=True,
        contains_crs_or_transform=True,
        expected_inputs=("input point", "GRID center", "focus window", "field navigation metadata"),
        expected_outputs=("private coordinate-bearing JSON, CSV, TXT, and sidecar summaries",),
        required_reference_artifacts=(
            "frozen notebook coordinate-bearing CSV/JSON artifacts",
            "mapping between notebook coordinate files and app filesystem artifacts",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity_private",
        classification="private coordinate-bearing filesystem artifact inventory",
        artifact_class="PRIVATE_COORDINATE_ARTIFACT",
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="requires_inventory_reconciliation",
        blocker="Existing private app coordinate artifacts need a source/reference mapping before any parity claim.",
        recommended_next_action="Reconcile app private coordinate artifacts against frozen notebook coordinate artifacts in a later verifier-planning slice.",
        notes="Artifact presence remains separate from notebook-value parity and does not change redacted public DTO behavior.",
    ),
    PrivateMapArtifactInventoryItem(
        id="phase6_redaction_and_serving_policy",
        category="redaction_and_serving_policy",
        notebook_artifact_or_pattern=(
            "Notebook coordinate outputs are private artifacts, not public DTO payloads."
        ),
        current_app_artifact_or_pattern=(
            "PRD redaction contract | artifact serving policy | can_serve_artifact and "
            "serve_artifact_response boundary"
        ),
        source_status="exact_source_found",
        current_app_status=(
            "Project policy requires coordinate-bearing material to stay out of public DTOs "
            "and artifact serving unless allowed by the serving gate."
        ),
        parity_status="covered_by_existing_contract",
        contains_coordinates=False,
        contains_geometry=False,
        contains_bounds=False,
        contains_crs_or_transform=False,
        expected_inputs=("artifact metadata", "public DTO redaction rules", "artifact class"),
        expected_outputs=("private policy inventory report only",),
        required_reference_artifacts=(
            "redaction contract documentation",
            "artifact serving policy documentation",
        ),
        required_metadata=_COMMON_REQUIRED_METADATA,
        target_mode="notebook_parity_private",
        classification="private redaction and serving policy inventory",
        artifact_class="LOCAL_SENSITIVE",
        filesystem_only=True,
        http_servable=False,
        frontend_visible=False,
        downloadable_via_api=False,
        runtime_output_verified=False,
        notebook_value_parity_verified=False,
        implementation_status="no_action_needed_existing_contract",
        blocker="",
        recommended_next_action="Keep coordinate-bearing artifacts private unless a later user-approved phase changes the policy.",
        notes="Phase 6 documents the boundary only; it does not change API, frontend, or artifact-serving code.",
    ),
)


def get_phase_6_private_map_artifact_inventory() -> tuple[
    PrivateMapArtifactInventoryItem,
    ...
]:
    """Return the Phase 6 private coordinate/map artifact inventory."""

    return _INVENTORY


def write_phase_6_private_map_artifact_inventory_report(
    run_dir: str | Path,
    run_id: str,
    *,
    items: Iterable[PrivateMapArtifactInventoryItem] | None = None,
    report_relative_path: str | Path = PHASE_6_PRIVATE_MAP_ARTIFACT_REPORT_RELATIVE_PATH,
) -> Path:
    """Write a run-local Phase 6 inventory report without creating map artifacts."""

    report_items = tuple(items or _INVENTORY)
    report_path = resolve_run_output_path(run_dir, report_relative_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": PHASE_6_PRIVATE_MAP_ARTIFACT_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "items": [item.to_dict() for item in report_items],
        "counts_by_category": _counts_by("category", report_items),
        "counts_by_parity_status": _counts_by("parity_status", report_items),
        "counts_by_implementation_status": _counts_by(
            "implementation_status",
            report_items,
        ),
        "counts_by_artifact_class": _counts_by("artifact_class", report_items),
        "phase_6_runtime_changes": False,
        "public_exposure_changes": False,
        "notes": (
            "Phase 6 is inventory, private-output contract, safety-boundary, and "
            "verification-planning only. It does not create coordinate/map artifacts, "
            "change artifact serving, or claim notebook-value parity."
        ),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_path


def _counts_by(
    field_name: str,
    items: Iterable[PrivateMapArtifactInventoryItem],
) -> dict[str, int]:
    if field_name == "category":
        counts = {value: 0 for value in sorted(ALLOWED_CATEGORIES)}
    elif field_name == "parity_status":
        counts = {value: 0 for value in sorted(ALLOWED_PARITY_STATUSES)}
    elif field_name == "implementation_status":
        counts = {value: 0 for value in sorted(ALLOWED_IMPLEMENTATION_STATUSES)}
    elif field_name == "artifact_class":
        counts = {value: 0 for value in sorted(ALLOWED_ARTIFACT_CLASSES)}
    else:
        raise ValueError(f"unsupported count field: {field_name}")

    for item in items:
        counts[getattr(item, field_name)] += 1
    return counts
