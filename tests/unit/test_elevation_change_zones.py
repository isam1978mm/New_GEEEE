from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from app.pipeline.elevation_change.coregistration import coregister_elevation_pair
from app.pipeline.elevation_change.zones import (
    ANCHOR_ROLE,
    CANDIDATE_ROLE,
    MeasuredZone,
    ZoneGenerationError,
    assign_roles,
    erode_mask,
    generate_measured_zones,
    label_components,
    largest_inscribed_rectangle,
    rectangle_ring,
    zones_to_geojson,
)
from scripts.build_operator_local_depth_package import build_operator_local_depth_package
from scripts.extract_operator_depth_signals import extract_operator_depth_signals
from scripts.run_operator_local_depth_for_existing_run import (
    run_operator_depth_for_existing_run,
)

NODATA = -9999.0
SIZE = 200
PIXEL_M = 10.0
PIXEL_AREA_M2 = PIXEL_M * PIXEL_M
CRS = "EPSG:32613"
ORIGIN_X = 0.0
ORIGIN_Y = 2000.0
# The six-value affine used across the pipeline: x = a*col + c, y = e*row + f.
TRANSFORM = (PIXEL_M, 0.0, ORIGIN_X, 0.0, -PIXEL_M, ORIGIN_Y)

COVERS = {
    "shallow": (slice(30, 60), slice(30, 60), 0.50),
    "middle": (slice(30, 60), slice(110, 140), 0.90),
    "deep": (slice(120, 150), slice(120, 150), 1.40),
}


def _scene(*, noise_sigma_m: float = 0.05, datum_offset_m: float = 1.75, seed: int = 4242):
    rng = np.random.default_rng(seed)
    rows, cols = np.indices((SIZE, SIZE), dtype=np.float64)
    early = 500.0 + rows * 0.03 + cols * 0.01

    placed = np.zeros((SIZE, SIZE), dtype=np.float64)
    for row_slice, col_slice, thickness in COVERS.values():
        placed[row_slice, col_slice] = thickness

    late = early + placed + datum_offset_m
    early = early + rng.normal(0.0, noise_sigma_m, early.shape)
    late = late + rng.normal(0.0, noise_sigma_m, late.shape)
    return early, late, placed


def _measured_delta():
    early, late, placed = _scene()
    result = coregister_elevation_pair(early, late, nodata=NODATA)
    return result, placed


class TestErodeMask:
    def test_shrinks_by_the_requested_number_of_pixels(self) -> None:
        mask = np.zeros((20, 20), dtype=bool)
        mask[5:15, 5:15] = True

        eroded = erode_mask(mask, 2)

        assert eroded[7:13, 7:13].all()
        assert not eroded[6, 6]
        assert int(eroded.sum()) == 6 * 6

    def test_zero_pixels_is_a_passthrough(self) -> None:
        mask = np.zeros((10, 10), dtype=bool)
        mask[2:5, 2:5] = True
        assert np.array_equal(erode_mask(mask, 0), mask)

    def test_rejects_negative_erosion(self) -> None:
        with pytest.raises(ZoneGenerationError):
            erode_mask(np.ones((5, 5), dtype=bool), -1)

    def test_matches_the_extractor_implementation(self) -> None:
        # The extractor keeps a private copy that cannot be imported from app/.
        # If the two ever diverge, zones would be measured over different pixels
        # than the signal is read from.
        from scripts.extract_operator_depth_signals import _erode_mask

        rng = np.random.default_rng(3)
        mask = rng.random((40, 40)) > 0.3
        for pixels in (0, 1, 2, 3):
            assert np.array_equal(erode_mask(mask, pixels), _erode_mask(mask, pixels))


class TestLabelComponents:
    def test_separates_disjoint_regions(self) -> None:
        mask = np.zeros((30, 30), dtype=bool)
        mask[2:8, 2:8] = True
        mask[20:28, 20:28] = True

        components = label_components(mask)

        assert len(components) == 2
        # Largest first.
        assert int(components[0].sum()) == 8 * 8
        assert int(components[1].sum()) == 6 * 6

    def test_diagonal_touch_is_not_connected(self) -> None:
        mask = np.zeros((10, 10), dtype=bool)
        mask[2, 2] = True
        mask[3, 3] = True

        assert len(label_components(mask)) == 2

    def test_empty_mask_has_no_components(self) -> None:
        assert label_components(np.zeros((10, 10), dtype=bool)) == []


class TestLargestInscribedRectangle:
    def test_finds_an_exact_rectangle(self) -> None:
        mask = np.zeros((20, 20), dtype=bool)
        mask[4:12, 6:16] = True

        assert largest_inscribed_rectangle(mask) == (4, 12, 6, 16)

    def test_result_lies_entirely_inside_the_mask(self) -> None:
        rng = np.random.default_rng(17)
        mask = rng.random((40, 40)) > 0.25
        rectangle = largest_inscribed_rectangle(mask)
        assert rectangle is not None
        row_start, row_stop, col_start, col_stop = rectangle
        assert mask[row_start:row_stop, col_start:col_stop].all()

    def test_prefers_the_larger_of_two_rectangles(self) -> None:
        mask = np.zeros((30, 30), dtype=bool)
        mask[0:4, 0:4] = True
        mask[10:20, 10:25] = True

        assert largest_inscribed_rectangle(mask) == (10, 20, 10, 25)

    def test_empty_mask_returns_none(self) -> None:
        assert largest_inscribed_rectangle(np.zeros((5, 5), dtype=bool)) is None


class TestRectangleRing:
    def test_ring_is_closed_and_has_five_positions(self) -> None:
        ring = rectangle_ring(
            row_start=0, row_stop=10, col_start=0, col_stop=10, transform=TRANSFORM
        )
        assert len(ring) == 5
        assert ring[0] == ring[-1]

    def test_maps_pixel_edges_to_projected_coordinates(self) -> None:
        ring = rectangle_ring(
            row_start=0, row_stop=10, col_start=0, col_stop=10, transform=TRANSFORM
        )
        xs = [position[0] for position in ring]
        ys = [position[1] for position in ring]
        assert min(xs) == pytest.approx(ORIGIN_X)
        assert max(xs) == pytest.approx(ORIGIN_X + 10 * PIXEL_M)
        assert max(ys) == pytest.approx(ORIGIN_Y)
        assert min(ys) == pytest.approx(ORIGIN_Y - 10 * PIXEL_M)

    def test_has_at_least_three_distinct_positions(self) -> None:
        ring = rectangle_ring(
            row_start=3, row_stop=9, col_start=4, col_stop=11, transform=TRANSFORM
        )
        distinct = {(position[0], position[1]) for position in ring[:-1]}
        assert len(distinct) >= 3

    def test_rejects_a_malformed_transform(self) -> None:
        with pytest.raises(ZoneGenerationError):
            rectangle_ring(
                row_start=0, row_stop=1, col_start=0, col_stop=1, transform=(1.0, 2.0)
            )


class TestGenerateMeasuredZones:
    def test_finds_the_three_placed_covers(self) -> None:
        result, _ = _measured_delta()

        zones = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
        )

        assert len(zones) >= 3
        measured = sorted(zone.thickness.mean_change_m for zone in zones)
        for expected in (0.50, 0.90, 1.40):
            assert any(abs(value - expected) < 0.08 for value in measured), (
                f"no zone near {expected}: {measured}"
            )

    def test_every_zone_lies_on_genuinely_raised_ground(self) -> None:
        result, placed = _measured_delta()

        zones = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
        )

        for zone in zones:
            covered = placed[
                zone.row_start : zone.row_stop, zone.col_start : zone.col_stop
            ]
            # The conservative interior rectangle must never straddle the edge of
            # a cover, otherwise the measured depth is an average of two levels.
            assert covered.min() > 0.0
            assert covered.min() == pytest.approx(covered.max())

    def test_zones_do_not_overlap(self) -> None:
        result, _ = _measured_delta()

        zones = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
        )

        occupancy = np.zeros((SIZE, SIZE), dtype=np.int32)
        for zone in zones:
            occupancy += zone.mask((SIZE, SIZE)).astype(np.int32)
        assert occupancy.max() <= 1

    def test_returns_nothing_when_no_material_was_placed(self) -> None:
        rng = np.random.default_rng(5)
        flat = rng.normal(0.0, 0.05, (SIZE, SIZE))

        zones = generate_measured_zones(
            flat, sigma_stable_m=0.05, pixel_area_m2=PIXEL_AREA_M2
        )

        assert zones == []

    def test_collapses_zones_that_are_too_similar_in_depth(self) -> None:
        result, _ = _measured_delta()

        zones = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
            minimum_separation_m=5.0,
        )

        assert len(zones) == 1

    def test_rejects_a_single_band(self) -> None:
        with pytest.raises(ZoneGenerationError):
            generate_measured_zones(
                np.zeros((10, 10)), sigma_stable_m=0.1, pixel_area_m2=1.0, band_count=1
            )


class TestAssignRoles:
    def _zones(self, depths: list[float]) -> list[MeasuredZone]:
        result, _ = _measured_delta()
        base = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
        )
        return base[: len(depths)]

    def test_withholds_the_middle_zone_as_the_candidate(self) -> None:
        result, _ = _measured_delta()
        zones = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
        )

        assigned = assign_roles(zones, withhold_for_validation=True)

        anchors = [zone for zone in assigned if zone.role == ANCHOR_ROLE]
        candidates = [zone for zone in assigned if zone.role == CANDIDATE_ROLE]
        assert len(candidates) == 1
        assert len(anchors) >= 2

        candidate_depth = candidates[0].thickness.mean_change_m
        anchor_depths = [zone.thickness.mean_change_m for zone in anchors]
        # The withheld zone must be interpolatable, not an extreme, or the engine
        # would abstain by design and the check would prove nothing.
        assert min(anchor_depths) < candidate_depth < max(anchor_depths)

    def test_can_keep_every_zone_as_an_anchor(self) -> None:
        result, _ = _measured_delta()
        zones = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
        )

        assigned = assign_roles(zones, withhold_for_validation=False)

        assert all(zone.role == ANCHOR_ROLE for zone in assigned)

    def test_refuses_when_too_few_zones_to_withhold(self) -> None:
        result, _ = _measured_delta()
        zones = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
        )

        with pytest.raises(ZoneGenerationError, match="at least 3"):
            assign_roles(zones[:2], withhold_for_validation=True)

    def test_refuses_a_single_zone(self) -> None:
        result, _ = _measured_delta()
        zones = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
        )

        with pytest.raises(ZoneGenerationError, match="at least 2"):
            assign_roles(zones[:1], withhold_for_validation=False)


def _generated_geojson() -> dict:
    result, _ = _measured_delta()
    zones = generate_measured_zones(
        result.delta_m,
        sigma_stable_m=result.stats.sigma_m,
        pixel_area_m2=PIXEL_AREA_M2,
    )
    return zones_to_geojson(
        assign_roles(zones, withhold_for_validation=True),
        transform=TRANSFORM,
        crs=CRS,
    )


class TestGeneratedGeojsonSatisfiesThePreflight:
    """Mirrors every rule in frontend-v2/src/app/localDepthPreflight.ts.

    The preflight is the gate a real operator file must pass. A generated file
    that cannot pass it would be useless no matter how good the measurement is.
    """

    def test_is_a_non_empty_feature_collection(self) -> None:
        payload = _generated_geojson()
        assert payload["type"] == "FeatureCollection"
        assert isinstance(payload["features"], list)
        assert payload["features"]

    def test_is_never_marked_template_only(self) -> None:
        assert _generated_geojson().get("template_only") is not True

    def test_carries_no_placeholder_identifiers(self) -> None:
        for feature in _generated_geojson()["features"]:
            assert "replace-with" not in feature["properties"]["feature_id"]

    def test_feature_ids_are_unique_and_non_empty(self) -> None:
        ids = [
            feature["properties"]["feature_id"]
            for feature in _generated_geojson()["features"]
        ]
        assert all(str(value).strip() for value in ids)
        assert len(set(ids)) == len(ids)

    def test_roles_are_supported(self) -> None:
        for feature in _generated_geojson()["features"]:
            assert feature["properties"]["role"] in {ANCHOR_ROLE, CANDIDATE_ROLE}

    def test_anchor_depths_are_ordered_and_non_negative(self) -> None:
        for feature in _generated_geojson()["features"]:
            properties = feature["properties"]
            if properties["role"] != ANCHOR_ROLE:
                continue
            minimum = properties["depth_min_m"]
            best = properties["depth_best_m"]
            maximum = properties["depth_max_m"]
            assert all(isinstance(value, float) for value in (minimum, best, maximum))
            assert 0 <= minimum <= best <= maximum

    def test_has_two_anchors_one_candidate_and_distinct_depths(self) -> None:
        features = _generated_geojson()["features"]
        anchors = [f for f in features if f["properties"]["role"] == ANCHOR_ROLE]
        candidates = [f for f in features if f["properties"]["role"] == CANDIDATE_ROLE]

        assert len(anchors) >= 2
        assert len(candidates) >= 1
        best_depths = {f"{f['properties']['depth_best_m']:.15g}" for f in anchors}
        assert len(best_depths) >= 2

    def test_geometry_rings_are_closed_and_valid(self) -> None:
        for feature in _generated_geojson()["features"]:
            geometry = feature["geometry"]
            assert geometry["type"] == "Polygon"
            for ring in geometry["coordinates"]:
                assert len(ring) >= 4
                assert ring[0] == ring[-1]
                distinct = {(position[0], position[1]) for position in ring[:-1]}
                assert len(distinct) >= 3
                for position in ring:
                    assert len(position) >= 2
                    assert all(np.isfinite(value) for value in position[:2])

    def test_candidates_carry_no_supplied_depth_fields(self) -> None:
        # A candidate holding depth_best_m would be silently promoted to truth.
        for feature in _generated_geojson()["features"]:
            properties = feature["properties"]
            if properties["role"] == CANDIDATE_ROLE:
                assert "depth_min_m" not in properties
                assert "depth_best_m" not in properties
                assert "depth_max_m" not in properties

    def test_records_that_depths_are_not_operator_survey_records(self) -> None:
        payload = _generated_geojson()
        assert payload["generated_by"] == "measured_elevation_change_v1"
        provenance = " ".join(payload["provenance"]).lower()
        assert "not operator survey records" in provenance
        assert "not depth to a buried object" in provenance


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_correlated_signal_raster(run_dir: Path, placed: np.ndarray) -> None:
    """A radar raster whose value tracks the placed thickness.

    This is a plumbing fixture, not a physical claim: it lets the test prove the
    generated zones drive the real engine end to end. Whether Sentinel-1 actually
    tracks depth this way is exactly what the held-out site work has to decide.
    """

    run_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(99)
    signal = (2.0 + 3.0 * placed + rng.normal(0.0, 0.01, placed.shape)).astype(np.float32)
    with rasterio.open(
        run_dir / "logRatio_dB.tif",
        "w",
        driver="GTiff",
        width=SIZE,
        height=SIZE,
        count=1,
        dtype="float32",
        crs=CRS,
        transform=from_origin(ORIGIN_X, ORIGIN_Y, PIXEL_M, PIXEL_M),
        nodata=NODATA,
    ) as dataset:
        dataset.write(signal, 1)


class TestEndToEndThroughTheExistingEngine:
    """The generated file must drive the shipped engine with no changes to it."""

    def _run(self, tmp_path: Path):
        result, placed = _measured_delta()
        zones = generate_measured_zones(
            result.delta_m,
            sigma_stable_m=result.stats.sigma_m,
            pixel_area_m2=PIXEL_AREA_M2,
        )
        assigned = assign_roles(zones, withhold_for_validation=True)
        payload = zones_to_geojson(assigned, transform=TRANSFORM, crs=CRS)

        run_dir = tmp_path / "run"
        _write_correlated_signal_raster(run_dir, placed)
        _write_json(
            run_dir / "QA" / "run_quality" / "run_quality_summary.json",
            {
                "schema": "run_quality_summary_v1",
                "stage": "run_quality",
                "status": "PASS",
                "is_usable": True,
            },
        )
        polygons_path = tmp_path / "generated_zones.geojson"
        _write_json(polygons_path, payload)

        extraction_dir = tmp_path / "extracted"
        extract_operator_depth_signals(
            run_dir=run_dir,
            polygons_path=polygons_path,
            output_dir=extraction_dir,
            site_id="synthetic-elevation-site",
            method_version="measured_elevation_change_v1",
            calibration_dataset_version="public_elevation_change_v1",
            input_crs=CRS,
            erosion_pixels=2,
            minimum_valid_pixels=20,
        )
        package_dir = tmp_path / "package"
        build_operator_local_depth_package(
            config_path=extraction_dir / "operator_depth_config.json",
            output_dir=package_dir,
        )
        execution = run_operator_depth_for_existing_run(
            run_dir=run_dir,
            package_dir=package_dir,
            candidate_input=extraction_dir / "operator_depth_candidates.json",
        )
        return assigned, execution, run_dir

    def test_generated_zones_drive_the_engine_to_an_estimate(self, tmp_path: Path) -> None:
        _, execution, _ = self._run(tmp_path)

        assert execution["candidate_count"] >= 1
        assert execution["estimated_count"] >= 1
        assert execution["method_kind"] == "operator_scalar_interpolation_v1"

    def test_withheld_zone_is_predicted_close_to_its_measured_depth(
        self, tmp_path: Path
    ) -> None:
        assigned, _, run_dir = self._run(tmp_path)

        withheld = next(zone for zone in assigned if zone.role == CANDIDATE_ROLE)
        estimates_path = run_dir / "depth" / "depth_estimates.csv"
        rows = [
            line.split(",")
            for line in estimates_path.read_text(encoding="utf-8").splitlines()[1:]
            if line.strip()
        ]
        by_id = {row[0]: row for row in rows}
        row = by_id[withheld.zone_id]

        assert row[1] in {"calibrated_range", "validated_range"}
        predicted_best = float(row[3])
        measured_best = withheld.thickness.mean_change_m
        assert predicted_best == pytest.approx(measured_best, abs=0.15)

    def test_engine_source_files_were_not_modified(self) -> None:
        # The whole point of generating the operator file rather than a new code
        # path is that the shipped engine stays untouched.
        repository_root = Path(__file__).resolve().parents[2]
        engine = (repository_root / "app" / "pipeline" / "depth" / "interpolation.py").read_text(
            encoding="utf-8"
        )
        assert "elevation" not in engine.lower()
        assert 'OPERATOR_METHOD_KIND = "operator_scalar_interpolation_v1"' in engine
