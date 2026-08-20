from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.pipeline.depth.package import (
    MANIFEST_NAME,
    _required_text,
    _verify_checksums,
    _warnings,
)
from app.pipeline.depth.schema import RecordedDepthMeasurement

RECORDED_PACKAGE_SCHEMA_VERSION = "recorded_depth_package_v1"
RECORDED_METHOD_KIND = "operator_recorded_zone_lookup_v1"


class RecordedDepthPackageError(ValueError):
    """Raised when a reviewed recorded-depth package is absent or invalid."""


@dataclass(frozen=True, slots=True)
class RecordedDepthZone:
    zone_id: str
    measurement: RecordedDepthMeasurement
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RecordedDepthPackage:
    root: Path
    method_version: str
    record_dataset_version: str
    site_id: str
    review_status: str
    zones: dict[str, RecordedDepthZone]
    warnings: tuple[str, ...]

    def zone(self, zone_id: str) -> RecordedDepthZone | None:
        return self.zones.get(zone_id)

    def public_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": RECORDED_PACKAGE_SCHEMA_VERSION,
            "method_kind": RECORDED_METHOD_KIND,
            "method_version": self.method_version,
            "record_dataset_version": self.record_dataset_version,
            "site_id": self.site_id,
            "review_status": self.review_status,
            "zone_count": len(self.zones),
            "warnings": list(self.warnings),
        }


def load_recorded_depth_package(root: Path) -> RecordedDepthPackage:
    root = Path(root)
    if not root.is_dir():
        raise RecordedDepthPackageError("recorded depth package directory does not exist")

    try:
        _verify_checksums(root)
    except ValueError as exc:
        raise RecordedDepthPackageError(str(exc)) from exc

    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise RecordedDepthPackageError(f"missing {MANIFEST_NAME}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecordedDepthPackageError("unreadable recorded depth manifest") from exc
    if not isinstance(payload, dict):
        raise RecordedDepthPackageError("recorded depth manifest must be a JSON object")
    if payload.get("schema_version") != RECORDED_PACKAGE_SCHEMA_VERSION:
        raise RecordedDepthPackageError("unsupported recorded depth package schema")
    if payload.get("method_kind") != RECORDED_METHOD_KIND:
        raise RecordedDepthPackageError("unsupported recorded depth method kind")

    review_status = _required_text(payload, "review_status")
    if review_status != "reviewed":
        raise RecordedDepthPackageError("review_status must be reviewed")

    raw_zones = payload.get("zones")
    if not isinstance(raw_zones, list) or not raw_zones:
        raise RecordedDepthPackageError("package must contain at least one reviewed zone")

    zones: dict[str, RecordedDepthZone] = {}
    for raw_zone in raw_zones:
        if not isinstance(raw_zone, dict):
            raise RecordedDepthPackageError("zone entry must be a JSON object")
        zone_id = _required_text(raw_zone, "zone_id")
        if zone_id in zones:
            raise RecordedDepthPackageError(f"duplicate zone_id: {zone_id}")
        try:
            measurement = RecordedDepthMeasurement.from_mapping(raw_zone)
        except ValueError as exc:
            raise RecordedDepthPackageError(
                f"invalid recorded measurement for zone {zone_id}"
            ) from exc
        zones[zone_id] = RecordedDepthZone(
            zone_id=zone_id,
            measurement=measurement,
            warnings=_warnings(raw_zone.get("warnings")),
        )

    return RecordedDepthPackage(
        root=root.resolve(),
        method_version=_required_text(payload, "method_version"),
        record_dataset_version=_required_text(payload, "record_dataset_version"),
        site_id=_required_text(payload, "site_id"),
        review_status=review_status,
        zones=zones,
        warnings=_warnings(payload.get("warnings")),
    )
