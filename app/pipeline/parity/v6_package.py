from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

from app.pipeline.parity import (
    ParityManifestEntry,
    ensure_standard_parity_dirs,
    resolve_parity_output_path,
    resolve_run_output_path,
    write_parity_manifest,
)


V6_PACKAGE_IMPORT_SCHEMA_VERSION = "v6_package_import_manifest_v1"
V6_REBUILT_ZIP_NAME = "paid_archive_request_candidate_package_FINAL_v6_ZONES_QUOTES.zip"
TIMESTAMPED_TOP25_PREFIX = "lawful_gee_candidate_scout_top_25_"

V6_REQUIRED_INPUT_FILES = (
    "top25_enhanced_v6.csv",
    "top25_enhanced_v6.geojson",
    "quality_diagnostics_all_cells_v6.csv",
    "stable_candidate_priority_list_v6.csv",
    "request_zones_v6.csv",
    "request_zones_v6.geojson",
    "paid_imagery_quote_template_v6.csv",
    "paid_imagery_quote_comparison_v6.csv",
    "paid_archive_request_summary.txt",
    "visual_inspection_map.html",
)

CSV_REQUIRED_COLUMN_GROUPS = {
    "top25_enhanced_v6.csv": (
        ("candidate_id", "object_id", "id"),
        ("candidate_score", "review_priority_score"),
    ),
    "stable_candidate_priority_list_v6.csv": (
        ("candidate_id", "object_id", "id"),
        ("review_priority_score", "candidate_score"),
    ),
    "quality_diagnostics_all_cells_v6.csv": (
        ("cell_id", "candidate_id", "object_id", "id"),
    ),
    "request_zones_v6.csv": (("zone_id",),),
    "paid_imagery_quote_template_v6.csv": (("zone_id",),),
    "paid_imagery_quote_comparison_v6.csv": (("zone_id",),),
}

GEOJSON_FILES = {
    "top25_enhanced_v6.geojson",
    "request_zones_v6.geojson",
}


class V6PackageValidationError(ValueError):
    """Raised when a v6 package cannot be imported as notebook parity data."""


@dataclass(frozen=True)
class V6PackageImportResult:
    import_manifest_path: Path
    parity_manifest_path: Path
    rebuilt_zip_path: Path | None
    package_files: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class _SourceFile:
    name: str
    bytes_data: bytes
    source_path: str


def import_v6_package(
    source_path: str | Path,
    *,
    run_dir: str | Path,
    run_id: str,
    rebuild_zip: bool = False,
) -> V6PackageImportResult:
    """Import a v6 notebook package directory or zip into the parity tree."""

    source = Path(source_path)
    source_type, source_files, warnings = _read_source_files(source)
    missing_required_files = _missing_required_files(source_files)
    if missing_required_files:
        raise V6PackageValidationError(
            "missing required v6 package files: " + ", ".join(missing_required_files)
        )

    _validate_source_files(source_files)
    ensure_standard_parity_dirs(run_dir)

    imported_items = []
    entries = []
    for name in _ordered_import_names(source_files):
        source_file = source_files[name]
        parity_relative = _parity_relative_path(name)
        parity_path = resolve_parity_output_path(run_dir, parity_relative)
        parity_path.parent.mkdir(parents=True, exist_ok=True)
        parity_path.write_bytes(source_file.bytes_data)

        digest = _sha256_bytes(source_file.bytes_data)
        package_item = {
            "file_name": name,
            "parity_path": f"parity/{Path(parity_relative).as_posix()}",
            "sha256": digest,
            "size_bytes": len(source_file.bytes_data),
            "family": _family_for_file(name),
            "validation_status": "valid",
        }
        imported_items.append(package_item)
        entries.append(
            _parity_entry_for_file(
                name=name,
                source_path=source_file.source_path,
                parity_path=package_item["parity_path"],
            )
        )

    rebuilt_zip_path: Path | None = None
    rebuilt_zip_sha256: str | None = None
    rebuilt_zip_run_path: str | None = None
    if rebuild_zip:
        rebuilt_zip_path = _write_rebuilt_zip(
            run_dir=Path(run_dir),
            source_files=source_files,
            import_names=_ordered_import_names(source_files),
        )
        rebuilt_zip_sha256 = _sha256_path(rebuilt_zip_path)
        rebuilt_zip_run_path = f"parity/root/{V6_REBUILT_ZIP_NAME}"
        entries.append(
            ParityManifestEntry(
                source_path=str(source),
                parity_path=rebuilt_zip_run_path,
                notebook_name_or_pattern=V6_REBUILT_ZIP_NAME,
                family="v6 candidate package outputs",
                classification="notebook-parity",
                artifact_class="FILESYSTEM_ONLY",
                target_mode="notebook_parity",
                http_servable=False,
                requires_coordinates=True,
                runtime_output_verified=True,
                notebook_value_parity_verified=False,
                notes="Rebuilt v6 notebook package zip with original member filenames preserved.",
            )
        )

    import_manifest_path = _write_import_manifest(
        run_dir=Path(run_dir),
        run_id=run_id,
        source_type=source_type,
        source_path=str(source),
        package_files=imported_items,
        missing_required_files=missing_required_files,
        warnings=warnings,
        rebuilt_zip_path=rebuilt_zip_run_path,
        rebuilt_zip_sha256=rebuilt_zip_sha256,
    )
    parity_manifest_path = write_parity_manifest(
        run_dir,
        run_id,
        entries,
        manifest_name="parity_manifest.json",
    )

    return V6PackageImportResult(
        import_manifest_path=import_manifest_path,
        parity_manifest_path=parity_manifest_path,
        rebuilt_zip_path=rebuilt_zip_path,
        package_files=tuple(imported_items),
    )


def _read_source_files(source: Path) -> tuple[str, dict[str, _SourceFile], list[str]]:
    if source.is_dir():
        source_files: dict[str, _SourceFile] = {}
        warnings: list[str] = []
        for child in sorted(source.iterdir()):
            if child.is_dir():
                warnings.append(f"ignored directory in v6 package source: {child.name}")
                continue
            source_files[child.name] = _SourceFile(
                name=child.name,
                bytes_data=child.read_bytes(),
                source_path=str(child),
            )
        return "directory", source_files, warnings

    if source.is_file() and source.suffix.lower() == ".zip":
        return "zip", _read_zip_source_files(source), []

    raise V6PackageValidationError("v6 package source must be a directory or zip file")


def _read_zip_source_files(source_zip: Path) -> dict[str, _SourceFile]:
    source_files: dict[str, _SourceFile] = {}
    with zipfile.ZipFile(source_zip) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            member_path = PurePosixPath(info.filename)
            if (
                info.filename.startswith("/")
                or ".." in member_path.parts
                or len(member_path.parts) != 1
            ):
                raise V6PackageValidationError(
                    f"zip path traversal or nested member blocked: {info.filename}"
                )
            name = member_path.name
            if name in source_files:
                raise V6PackageValidationError(f"duplicate zip member: {name}")
            source_files[name] = _SourceFile(
                name=name,
                bytes_data=archive.read(info),
                source_path=f"{source_zip}!{name}",
            )
    return source_files


def _missing_required_files(source_files: dict[str, _SourceFile]) -> list[str]:
    names = set(source_files)
    missing = [name for name in V6_REQUIRED_INPUT_FILES if name not in names]
    if not _timestamped_top25_names(source_files, ".csv"):
        missing.append(f"{TIMESTAMPED_TOP25_PREFIX}*.csv")
    if not _timestamped_top25_names(source_files, ".geojson"):
        missing.append(f"{TIMESTAMPED_TOP25_PREFIX}*.geojson")
    return missing


def _timestamped_top25_names(
    source_files: dict[str, _SourceFile],
    suffix: str,
) -> list[str]:
    return sorted(
        name
        for name in source_files
        if name.startswith(TIMESTAMPED_TOP25_PREFIX) and name.endswith(suffix)
    )


def _ordered_import_names(source_files: dict[str, _SourceFile]) -> tuple[str, ...]:
    timestamped = _timestamped_top25_names(
        source_files,
        ".csv",
    ) + _timestamped_top25_names(source_files, ".geojson")
    return tuple(sorted(timestamped) + list(V6_REQUIRED_INPUT_FILES))


def _validate_source_files(source_files: dict[str, _SourceFile]) -> None:
    for name in _timestamped_top25_names(source_files, ".csv"):
        _validate_csv_columns(name, source_files[name].bytes_data, (("candidate_id", "object_id", "id"),))
    for name in CSV_REQUIRED_COLUMN_GROUPS:
        _validate_csv_columns(name, source_files[name].bytes_data, CSV_REQUIRED_COLUMN_GROUPS[name])

    for name in _timestamped_top25_names(source_files, ".geojson"):
        _validate_geojson(name, source_files[name].bytes_data)
    for name in GEOJSON_FILES:
        _validate_geojson(name, source_files[name].bytes_data)


def _validate_csv_columns(
    name: str,
    bytes_data: bytes,
    required_groups: tuple[tuple[str, ...], ...],
) -> None:
    text = bytes_data.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    fieldnames = set(reader.fieldnames or [])
    missing_groups = [
        group for group in required_groups if not any(column in fieldnames for column in group)
    ]
    if missing_groups:
        details = "; ".join("requires one of " + ", ".join(group) for group in missing_groups)
        raise V6PackageValidationError(f"CSV schema validation failed for {name}: {details}")


def _validate_geojson(name: str, bytes_data: bytes) -> None:
    try:
        parsed = json.loads(bytes_data.decode("utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise V6PackageValidationError(f"GeoJSON validation failed for {name}: invalid JSON") from exc
    if not isinstance(parsed, dict) or parsed.get("type") != "FeatureCollection":
        raise V6PackageValidationError(
            f"GeoJSON validation failed for {name}: expected FeatureCollection"
        )
    if not isinstance(parsed.get("features"), list):
        raise V6PackageValidationError(
            f"GeoJSON validation failed for {name}: expected features array"
        )


def _parity_relative_path(name: str) -> str:
    if name == "visual_inspection_map.html":
        return f"maps/{name}"
    return f"root/{name}"


def _family_for_file(name: str) -> str:
    if name == "paid_archive_request_summary.txt":
        return "v6 candidate package outputs"
    if name == "visual_inspection_map.html" or name.endswith(".geojson"):
        return "coordinate/map/KMZ/GeoJSON outputs"
    if name.startswith(TIMESTAMPED_TOP25_PREFIX) or name in {
        "top25_enhanced_v6.csv",
        "quality_diagnostics_all_cells_v6.csv",
        "stable_candidate_priority_list_v6.csv",
    }:
        return "candidate/ranking CSV + GeoJSON outputs"
    if name.startswith("request_zones_v6"):
        return "request-zone outputs"
    if name.startswith("paid_imagery_quote_"):
        return "quote-template/comparison outputs"
    return "v6 candidate package outputs"


def _parity_entry_for_file(
    *,
    name: str,
    source_path: str,
    parity_path: str,
) -> ParityManifestEntry:
    coordinate_bearing = name.endswith(".geojson") or name == "visual_inspection_map.html"
    return ParityManifestEntry(
        source_path=source_path,
        parity_path=parity_path,
        notebook_name_or_pattern=name,
        family=_family_for_file(name),
        classification="coordinate-bearing" if coordinate_bearing else "notebook-parity",
        artifact_class="FILESYSTEM_ONLY",
        target_mode="notebook_parity",
        http_servable=False,
        requires_coordinates=coordinate_bearing,
        runtime_output_verified=True,
        notebook_value_parity_verified=False,
        notes="Imported v6 notebook package file with original filename preserved.",
    )


def _write_rebuilt_zip(
    *,
    run_dir: Path,
    source_files: dict[str, _SourceFile],
    import_names: tuple[str, ...],
) -> Path:
    rebuilt_path = resolve_parity_output_path(run_dir, f"root/{V6_REBUILT_ZIP_NAME}")
    rebuilt_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(rebuilt_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in import_names:
            archive.writestr(name, source_files[name].bytes_data)
    return rebuilt_path


def _write_import_manifest(
    *,
    run_dir: Path,
    run_id: str,
    source_type: str,
    source_path: str,
    package_files: list[dict[str, object]],
    missing_required_files: list[str],
    warnings: list[str],
    rebuilt_zip_path: str | None,
    rebuilt_zip_sha256: str | None,
) -> Path:
    manifest_path = resolve_run_output_path(
        run_dir,
        "manifests/v6_package_import_manifest.json",
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": V6_PACKAGE_IMPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "imported_at": datetime.now(UTC).isoformat(),
        "source_type": source_type,
        "source_path": source_path,
        "package_files": package_files,
        "validation_status": "valid",
        "missing_required_files": missing_required_files,
        "warnings": warnings,
        "rebuilt_zip_path": rebuilt_zip_path,
        "rebuilt_zip_sha256": rebuilt_zip_sha256,
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _sha256_bytes(bytes_data: bytes) -> str:
    return hashlib.sha256(bytes_data).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        shutil.copyfileobj(handle, _HashWriter(digest))
    return digest.hexdigest()


class _HashWriter:
    def __init__(self, digest: "hashlib._Hash") -> None:
        self._digest = digest

    def write(self, data: bytes) -> int:
        self._digest.update(data)
        return len(data)
