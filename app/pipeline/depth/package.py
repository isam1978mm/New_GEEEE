from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.pipeline.depth.schema import DepthRange

PACKAGE_SCHEMA_VERSION = "local_depth_package_v1"
PACKAGE_METHOD_KIND = "operator_zone_lookup_v1"
MANIFEST_NAME = "depth_method_manifest.json"
CHECKSUMS_NAME = "checksums.sha256"


class LocalDepthPackageError(ValueError):
    """Raised when a private local depth package is absent or invalid."""


@dataclass(frozen=True, slots=True)
class LocalDepthZone:
    zone_id: str
    depth_range: DepthRange
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LocalDepthPackage:
    root: Path
    method_version: str
    calibration_dataset_version: str
    site_id: str
    validation_status: str
    allow_run_quality_warning: bool
    zones: dict[str, LocalDepthZone]
    warnings: tuple[str, ...]

    @property
    def output_status(self) -> str:
        return "validated_range" if self.validation_status == "validated" else "calibrated_range"

    @property
    def depth_quality(self) -> str:
        return "validated_local" if self.validation_status == "validated" else "provisional_local"

    def zone(self, zone_id: str) -> LocalDepthZone | None:
        return self.zones.get(zone_id)

    def public_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": PACKAGE_SCHEMA_VERSION,
            "method_kind": PACKAGE_METHOD_KIND,
            "method_version": self.method_version,
            "calibration_dataset_version": self.calibration_dataset_version,
            "site_id": self.site_id,
            "validation_status": self.validation_status,
            "zone_count": len(self.zones),
            "allow_run_quality_warning": self.allow_run_quality_warning,
            "warnings": list(self.warnings),
        }


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise LocalDepthPackageError(f"missing package field: {key}")
    return value


def _warnings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise LocalDepthPackageError("package warnings must be a list")
    result: list[str] = []
    for item in value:
        warning = str(item or "").strip()
        if warning and warning not in result:
            result.append(warning)
    return tuple(result)


def _safe_package_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise LocalDepthPackageError("checksum path escapes package root")
    return candidate


def _verify_checksums(root: Path) -> None:
    checksum_path = root / CHECKSUMS_NAME
    if not checksum_path.is_file():
        raise LocalDepthPackageError(f"missing {CHECKSUMS_NAME}")

    verified = 0
    for raw_line in checksum_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise LocalDepthPackageError("invalid checksum line")
        expected, relative_path = parts
        relative_path = relative_path.lstrip("*").strip()
        if len(expected) != 64 or any(char not in "0123456789abcdefABCDEF" for char in expected):
            raise LocalDepthPackageError("invalid checksum digest")
        target = _safe_package_path(root, relative_path)
        if not target.is_file():
            raise LocalDepthPackageError(f"missing checksummed file: {relative_path}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual.lower() != expected.lower():
            raise LocalDepthPackageError(f"checksum mismatch: {relative_path}")
        verified += 1

    if verified <= 0:
        raise LocalDepthPackageError("no package files were checksummed")


def load_local_depth_package(root: Path) -> LocalDepthPackage:
    root = Path(root)
    if not root.is_dir():
        raise LocalDepthPackageError("local depth package directory does not exist")

    _verify_checksums(root)
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise LocalDepthPackageError(f"missing {MANIFEST_NAME}")

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalDepthPackageError("unreadable local depth manifest") from exc
    if not isinstance(payload, dict):
        raise LocalDepthPackageError("local depth manifest must be a JSON object")

    if payload.get("schema_version") != PACKAGE_SCHEMA_VERSION:
        raise LocalDepthPackageError("unsupported local depth package schema")
    if payload.get("method_kind") != PACKAGE_METHOD_KIND:
        raise LocalDepthPackageError("unsupported local depth method kind")

    validation_status = _required_text(payload, "validation_status")
    if validation_status not in {"provisional", "validated"}:
        raise LocalDepthPackageError("validation_status must be provisional or validated")

    raw_zones = payload.get("zones")
    if not isinstance(raw_zones, list) or not raw_zones:
        raise LocalDepthPackageError("package must contain at least one local zone")

    zones: dict[str, LocalDepthZone] = {}
    for raw_zone in raw_zones:
        if not isinstance(raw_zone, dict):
            raise LocalDepthPackageError("zone entry must be a JSON object")
        zone_id = _required_text(raw_zone, "zone_id")
        if zone_id in zones:
            raise LocalDepthPackageError(f"duplicate zone_id: {zone_id}")
        try:
            depth_range = DepthRange.from_mapping(raw_zone)
        except ValueError as exc:
            raise LocalDepthPackageError(f"invalid range for zone {zone_id}") from exc
        zones[zone_id] = LocalDepthZone(
            zone_id=zone_id,
            depth_range=depth_range,
            warnings=_warnings(raw_zone.get("warnings")),
        )

    return LocalDepthPackage(
        root=root.resolve(),
        method_version=_required_text(payload, "method_version"),
        calibration_dataset_version=_required_text(payload, "calibration_dataset_version"),
        site_id=_required_text(payload, "site_id"),
        validation_status=validation_status,
        allow_run_quality_warning=bool(payload.get("allow_run_quality_warning", False)),
        zones=zones,
        warnings=_warnings(payload.get("warnings")),
    )
