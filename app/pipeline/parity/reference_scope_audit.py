"""D1A — bundle-wide frozen reference scope audit (D1B source-locked baseline).

This module audits whether a frozen D1 reference bundle is *scope-complete*
against the ``notebooks/new.ipynb`` expected-output set. The D2 validator proved
manifest/file integrity; this audit answers a different question: which expected
notebook outputs are present, missing, or extra in the frozen bundle.

D1B source-lock: the expected-output baseline is no longer trusted blindly. Each
expected-output family carries a ``scope_tier`` so the audit can distinguish:

  * ``required_new_ipynb``          — outputs new.ipynb actually writes/registers
  * ``parked_v6``                   — V6 paid-archive/quote/request-zone package
                                      outputs (NOT produced by new.ipynb)
  * ``accepted_non_reproducible``   — intermediates production does not retain
  * ``tier2_source_recovery``       — real notebook outputs deferred to recovery
  * ``optional``                    — not-near-term / non-new.ipynb items

Default pass/fail is computed from ``required_new_ipynb`` outputs ONLY. Parked
V6 and accepted non-reproducible items never fail the required status.

The DEM expected set is source-locked from notebook ``save_tif`` evidence (see
:data:`DEM_SOURCE_LOCKED_OUTPUTS`): ``new.ipynb`` writes nine ``DEM_GEO8_TIFS``
rasters via ``save_tif(name, arr)`` -> ``{name}_640.tif``. It writes
``aspect_deg`` (not ``aspect``) and does NOT write ``tri`` or ``twi``.

It is local-only and read-only. It does NOT run the notebook, call Earth Engine,
modify the bundle, change DEM formulas, or add filename aliases.

Safety: the default summary is counts + family/tier names only. Raw relative
paths are surfaced only via the explicit, local-only ``detailed_report``.
"""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

REFERENCE_MANIFEST_NAME = "reference_manifest.json"
PARITY_DOC_RELATIVE = "docs/parity_expected_outputs.json"
SOURCELOCKED_DOC_RELATIVE = "docs/parity_expected_outputs_sourcelocked.json"

DEM_FAMILY = "DEM/terrain outputs"

# Scope tiers.
TIER_REQUIRED = "required_new_ipynb"
TIER_PARKED_V6 = "parked_v6"
TIER_ACCEPTED_NON_REPRODUCIBLE = "accepted_non_reproducible"
TIER_TIER2_RECOVERY = "tier2_source_recovery"
TIER_OPTIONAL = "optional"
ALL_TIERS = (
    TIER_REQUIRED,
    TIER_PARKED_V6,
    TIER_ACCEPTED_NON_REPRODUCIBLE,
    TIER_TIER2_RECOVERY,
    TIER_OPTIONAL,
)

# DEM expected outputs, source-locked from notebooks/new.ipynb save_tif evidence.
# save_tif(name, arr) writes os.path.join(DEM_GEO8_TIFS, f"{name}_640.tif").
DEM_SOURCE_LOCKED_OUTPUTS: tuple[str, ...] = (
    "DEM_GEO8_TIFS/DEM_640.tif",
    "DEM_GEO8_TIFS/slope_deg_640.tif",
    "DEM_GEO8_TIFS/aspect_deg_640.tif",
    "DEM_GEO8_TIFS/hillshade_0to1_640.tif",
    "DEM_GEO8_TIFS/roughness_100m_640.tif",
    "DEM_GEO8_TIFS/tpi_100m_640.tif",
    "DEM_GEO8_TIFS/curv_laplacian_640.tif",
    "DEM_GEO8_TIFS/curv_plan_640.tif",
    "DEM_GEO8_TIFS/curv_profile_640.tif",
)

# Object-table outputs, source-locked from notebooks/new.ipynb evidence (D1D).
# Cell 68 writes AI_OBJECT_TABLES/objects_index.csv from PCA candidate labels;
# cell 69 writes AI_OBJECT_TABLES/clusters_summary.csv from that same
# objects_index.csv. Both are real new.ipynb outputs (corrects the earlier bare
# names objects_index.csv / clusters_summary.csv to their AI_OBJECT_TABLES path).
OBJECT_TABLE_FAMILY = "AI object tables"
OBJECT_TABLE_ENTRY_ID = "object_extraction_outputs"
OBJECT_TABLE_SOURCE_LOCKED_OUTPUTS: tuple[str, ...] = (
    "AI_OBJECT_TABLES/objects_index.csv",
    "AI_OBJECT_TABLES/clusters_summary.csv",
)

# Reconciliation: scope_tier per parity-doc entry id. Justified by static
# notebooks/new.ipynb evidence collected during D1B.
TIER_BY_ENTRY_ID: dict[str, str] = {
    # Real new.ipynb outputs with app writers -> bundle must contain them.
    "dem_terrain_outputs": TIER_REQUIRED,
    "dem_curvature_variants": TIER_REQUIRED,
    "report_640_outputs": TIER_REQUIRED,
    "ai_ready_secret_outputs": TIER_REQUIRED,
    "hypercube_tensor_outputs": TIER_REQUIRED,
    "sar_radar_core_outputs": TIER_REQUIRED,
    "s2_optical_index_outputs": TIER_REQUIRED,
    "qa_grid_run_manifest_outputs": TIER_REQUIRED,
    # D1D: object tables are real new.ipynb outputs (cells 68/69) but were never
    # produced in the D1C export and cannot be regenerated same-run without
    # crossing notebook versions (export uses RADAR_*_v5 / FINAL_TESLA_V7_2; the
    # object pipeline reads RADM_* / GLOBAL_SAR_ARCHAEO + PCA NPYs, all absent).
    # Deferred to source recovery via a corrected same-run re-export.
    "object_extraction_outputs": TIER_TIER2_RECOVERY,
    # V6 paid-archive package family — NOT written by new.ipynb (names absent).
    "v6_candidate_package_outputs": TIER_PARKED_V6,
    "request_zone_outputs": TIER_PARKED_V6,
    "quote_template_comparison_outputs": TIER_PARKED_V6,
    "candidate_ranking_csv_geojson": TIER_PARKED_V6,
    "visual_inspection_map_html": TIER_PARKED_V6,
    # Production does not retain pre-RTC SAR intermediate groups.
    "pre_rtc_sar_intermediates": TIER_ACCEPTED_NON_REPRODUCIBLE,
    # Real notebook outputs missing from the app, deferred to source recovery.
    "sar_asc_desc_filtered_outputs": TIER_TIER2_RECOVERY,
    "panchromatic_optical_outputs": TIER_TIER2_RECOVERY,
    "ai_beh_broader_series": TIER_TIER2_RECOVERY,
    # Not-near-term / not retained new.ipynb outputs.
    "hypercube_resampled_filtered_missing": TIER_OPTIONAL,
    "classifier_neutral_current_outputs": TIER_OPTIONAL,
    "classifier_original_label_parity_outputs": TIER_OPTIONAL,
    "future_probability_only_classifier_outputs": TIER_OPTIONAL,
    "deep_learning_model_cells": TIER_OPTIONAL,
    "broken_model_constructor_cell": TIER_OPTIONAL,
    "coordinate_map_kmz_geojson_outputs": TIER_OPTIONAL,
    "focus_mask_outputs": TIER_OPTIONAL,
    "qa_sar_provenance_outputs": TIER_OPTIONAL,
    "qa_alignment_zero_pca_stack_outputs": TIER_OPTIONAL,
}
DEFAULT_TIER = TIER_OPTIONAL

STATUS_COMPLETE = "complete"
STATUS_INCOMPLETE = "incomplete"
STATUS_ERROR = "error"

# A token is a concrete output path/pattern (not prose) when it has no spaces
# and either contains a path separator or a file extension. ``*`` globs allowed.
_PATH_TOKEN = re.compile(r"^[^\s]+$")
_HAS_EXTENSION = re.compile(r"\.[A-Za-z0-9]{1,6}$")


@dataclass(frozen=True)
class ExpectedEntry:
    """One expected output path/pattern with its family and scope tier."""

    path: str
    family: str
    scope_tier: str


@dataclass(frozen=True)
class ScopeAuditResult:
    status: str
    # Required-tier counts drive the headline status.
    expected_required_count: int = 0
    present_required_count: int = 0
    missing_required_count: int = 0
    extra_count: int = 0
    # Required-tier breakdowns.
    missing_by_family: dict[str, int] = field(default_factory=dict)
    present_by_family: dict[str, int] = field(default_factory=dict)
    # Non-required tier counts (informational; never fail the status).
    counts_by_tier: dict[str, dict[str, int]] = field(default_factory=dict)
    # Detail-only (never in safe summary):
    missing_paths_by_family: dict[str, list[str]] = field(default_factory=dict)
    present_paths_by_family: dict[str, list[str]] = field(default_factory=dict)
    missing_paths_by_tier: dict[str, list[str]] = field(default_factory=dict)
    extra_paths: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def is_complete(self) -> bool:
        return self.status == STATUS_COMPLETE

    def safe_summary(self) -> dict[str, Any]:
        """Counts + family/tier names only. Never includes raw relative paths."""

        return {
            "status": self.status,
            "expected_required_count": self.expected_required_count,
            "present_required_count": self.present_required_count,
            "missing_required_count": self.missing_required_count,
            "extra_count": self.extra_count,
            "missing_by_family": dict(sorted(self.missing_by_family.items())),
            "present_by_family": dict(sorted(self.present_by_family.items())),
            "counts_by_tier": {
                tier: dict(sorted(counts.items()))
                for tier, counts in sorted(self.counts_by_tier.items())
            },
            "error": self.error,
        }

    def detailed_report(self) -> dict[str, Any]:
        report = self.safe_summary()
        report["missing_paths_by_family"] = {
            k: sorted(v) for k, v in sorted(self.missing_paths_by_family.items())
        }
        report["present_paths_by_family"] = {
            k: sorted(v) for k, v in sorted(self.present_paths_by_family.items())
        }
        report["missing_paths_by_tier"] = {
            k: sorted(v) for k, v in sorted(self.missing_paths_by_tier.items())
        }
        report["extra_paths"] = sorted(self.extra_paths)
        return report


def _error(message: str) -> ScopeAuditResult:
    return ScopeAuditResult(status=STATUS_ERROR, error=message)


# ---------------------------------------------------------------------------
# Expected-output set loading
# ---------------------------------------------------------------------------
def _is_path_token(token: object) -> bool:
    if not isinstance(token, str) or not token.strip():
        return False
    candidate = token.strip()
    if not _PATH_TOKEN.match(candidate):
        return False
    return ("/" in candidate) or bool(_HAS_EXTENSION.search(candidate))


def expected_entries_from_sourcelocked(doc: Mapping[str, Any]) -> list[ExpectedEntry]:
    """Read a D1B source-locked baseline file (the trusted format)."""

    entries: list[ExpectedEntry] = []
    for raw in doc.get("entries", []):
        if not isinstance(raw, Mapping):
            continue
        family = raw.get("family") or "unclassified"
        tier = raw.get("scope_tier") or DEFAULT_TIER
        for path in raw.get("paths", []):
            if isinstance(path, str) and path:
                entries.append(ExpectedEntry(path=path, family=str(family), scope_tier=str(tier)))
    return entries


def expected_entries_from_parity_doc(doc: Mapping[str, Any]) -> list[ExpectedEntry]:
    """Derive tiered entries from the raw (untrusted) parity doc.

    DEM is source-locked to :data:`DEM_SOURCE_LOCKED_OUTPUTS` and the object
    tables to :data:`OBJECT_TABLE_SOURCE_LOCKED_OUTPUTS`; the doc's tokens for
    those families are ignored in favour of notebook evidence. Each entry's tier
    comes from :data:`TIER_BY_ENTRY_ID`.
    """

    entries: list[ExpectedEntry] = []
    seen_dem = False
    for raw in doc.get("expected_outputs", []):
        if not isinstance(raw, Mapping):
            continue
        entry_id = raw.get("id")
        family = raw.get("family") or "unclassified"
        tier = TIER_BY_ENTRY_ID.get(str(entry_id), DEFAULT_TIER)

        if family == DEM_FAMILY:
            # Source-lock DEM from notebook evidence exactly once.
            if not seen_dem:
                for path in DEM_SOURCE_LOCKED_OUTPUTS:
                    entries.append(
                        ExpectedEntry(path=path, family=DEM_FAMILY, scope_tier=TIER_REQUIRED)
                    )
                seen_dem = True
            continue

        if str(entry_id) == OBJECT_TABLE_ENTRY_ID:
            # Source-lock object-table names to their AI_OBJECT_TABLES paths.
            for path in OBJECT_TABLE_SOURCE_LOCKED_OUTPUTS:
                entries.append(
                    ExpectedEntry(path=path, family=OBJECT_TABLE_FAMILY, scope_tier=tier)
                )
            continue

        tokens = raw.get("notebook_paths_or_patterns")
        if not isinstance(tokens, list):
            continue
        for token in tokens:
            if _is_path_token(token):
                entries.append(
                    ExpectedEntry(path=token, family=str(family), scope_tier=tier)
                )
    return entries


def _dedupe(entries: list[ExpectedEntry]) -> list[ExpectedEntry]:
    seen: set[str] = set()
    out: list[ExpectedEntry] = []
    for e in entries:
        if e.path in seen:
            continue
        seen.add(e.path)
        out.append(e)
    return out


def load_expected_entries(
    expected_outputs: Mapping[str, list[str]] | None = None,
    expected_outputs_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> list[ExpectedEntry]:
    # 1. Explicit mapping (tests): treat all as required tier.
    if expected_outputs is not None:
        entries = [
            ExpectedEntry(path=p, family=family, scope_tier=TIER_REQUIRED)
            for family, paths in expected_outputs.items()
            for p in paths
        ]
        return _dedupe(entries)

    # 2. Explicit file.
    if expected_outputs_path is not None:
        path = Path(expected_outputs_path)
        text = path.read_text(encoding="utf-8")
        doc = json.loads(text)
        if "entries" in doc:
            return _dedupe(expected_entries_from_sourcelocked(doc))
        return _dedupe(expected_entries_from_parity_doc(doc))

    # 3. Default: prefer the source-locked baseline, fall back to the raw doc.
    root = repo_root or Path(__file__).resolve().parents[3]
    sourcelocked = root / SOURCELOCKED_DOC_RELATIVE
    if sourcelocked.is_file():
        doc = json.loads(sourcelocked.read_text(encoding="utf-8"))
        return _dedupe(expected_entries_from_sourcelocked(doc))
    parity = root / PARITY_DOC_RELATIVE
    if parity.is_file():
        doc = json.loads(parity.read_text(encoding="utf-8"))
        return _dedupe(expected_entries_from_parity_doc(doc))
    # Last resort: DEM source-locked required set only.
    return [
        ExpectedEntry(path=p, family=DEM_FAMILY, scope_tier=TIER_REQUIRED)
        for p in DEM_SOURCE_LOCKED_OUTPUTS
    ]


# ---------------------------------------------------------------------------
# Bundle manifest loading
# ---------------------------------------------------------------------------
def _load_bundle_paths(bundle_dir: Path) -> tuple[list[str] | None, str | None]:
    if not bundle_dir.is_dir():
        return None, "Reference bundle directory does not exist."
    manifest_path = bundle_dir / REFERENCE_MANIFEST_NAME
    if not manifest_path.is_file():
        return None, f"{REFERENCE_MANIFEST_NAME} is missing from the bundle."
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"{REFERENCE_MANIFEST_NAME} could not be read or parsed: {exc}"
    if not isinstance(payload, Mapping):
        return None, f"{REFERENCE_MANIFEST_NAME} must contain a JSON object."
    files = payload.get("files")
    if not isinstance(files, list):
        return None, "Manifest 'files' must be a list."
    paths: list[str] = []
    for entry in files:
        if not isinstance(entry, Mapping):
            return None, "Manifest file entry must be an object."
        rel = entry.get("relative_path")
        if not isinstance(rel, str) or not rel:
            return None, "Manifest file entry has an invalid relative_path."
        paths.append(rel.replace("\\", "/"))
    return paths, None


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
def _match_bundle(pattern: str, bundle_set: set[str]) -> set[str]:
    normalized = pattern.replace("\\", "/")
    if "*" in normalized or "?" in normalized or "[" in normalized:
        return {p for p in bundle_set if fnmatch.fnmatch(p, normalized)}
    return {normalized} if normalized in bundle_set else set()


def audit_reference_scope(
    bundle_dir: str | Path,
    *,
    expected_outputs: Mapping[str, list[str]] | None = None,
    expected_outputs_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> ScopeAuditResult:
    """Audit a frozen D1 bundle's scope against expected notebook outputs.

    Headline ``status`` reflects ``required_new_ipynb`` outputs only. Parked V6
    and accepted non-reproducible items are reported but never fail the status.
    """

    bundle_root = Path(bundle_dir)
    bundle_paths, error = _load_bundle_paths(bundle_root)
    if error is not None:
        return _error(error)
    assert bundle_paths is not None

    try:
        entries = load_expected_entries(
            expected_outputs, expected_outputs_path, repo_root=repo_root
        )
    except (OSError, ValueError) as exc:
        return _error(f"Expected-output set could not be loaded: {exc}")

    bundle_set = set(bundle_paths)
    matched_bundle_paths: set[str] = set()

    present_by_family: dict[str, int] = {}
    missing_by_family: dict[str, int] = {}
    present_paths_by_family: dict[str, list[str]] = {}
    missing_paths_by_family: dict[str, list[str]] = {}
    missing_paths_by_tier: dict[str, list[str]] = {}
    counts_by_tier: dict[str, dict[str, int]] = {
        tier: {"expected": 0, "present": 0, "missing": 0} for tier in ALL_TIERS
    }

    for entry in entries:
        matches = _match_bundle(entry.path, bundle_set)
        tier_counts = counts_by_tier.setdefault(
            entry.scope_tier, {"expected": 0, "present": 0, "missing": 0}
        )
        tier_counts["expected"] += 1
        if matches:
            matched_bundle_paths.update(matches)
            tier_counts["present"] += 1
            if entry.scope_tier == TIER_REQUIRED:
                present_by_family[entry.family] = present_by_family.get(entry.family, 0) + 1
                present_paths_by_family.setdefault(entry.family, []).append(entry.path)
        else:
            tier_counts["missing"] += 1
            missing_paths_by_tier.setdefault(entry.scope_tier, []).append(entry.path)
            if entry.scope_tier == TIER_REQUIRED:
                missing_by_family[entry.family] = missing_by_family.get(entry.family, 0) + 1
                missing_paths_by_family.setdefault(entry.family, []).append(entry.path)

    required = counts_by_tier.get(TIER_REQUIRED, {"expected": 0, "present": 0, "missing": 0})
    extra_paths = sorted(bundle_set - matched_bundle_paths)

    status = STATUS_COMPLETE if required["missing"] == 0 else STATUS_INCOMPLETE
    return ScopeAuditResult(
        status=status,
        expected_required_count=required["expected"],
        present_required_count=required["present"],
        missing_required_count=required["missing"],
        extra_count=len(extra_paths),
        missing_by_family=missing_by_family,
        present_by_family=present_by_family,
        counts_by_tier=counts_by_tier,
        missing_paths_by_family=missing_paths_by_family,
        present_paths_by_family=present_paths_by_family,
        missing_paths_by_tier=missing_paths_by_tier,
        extra_paths=extra_paths,
    )
