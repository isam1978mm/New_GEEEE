from __future__ import annotations

import numpy as np
import pytest

from app.pipeline.elevation_change.coregistration import (
    CoregistrationError,
    coregister_elevation_pair,
    estimate_stable_ground,
    nmad,
    select_stable_mask,
    shared_data_fraction,
)
from app.pipeline.elevation_change.thickness import (
    DEFAULT_CORRELATION_LENGTH_M,
    ThicknessError,
    correlated_mean_uncertainty,
    measure_polygon_thickness,
    significant_change_mask,
)

NODATA = -9999.0
PIXEL_M = 10.0
PIXEL_AREA_M2 = PIXEL_M * PIXEL_M


def _baseline_surface(size: int = 200) -> np.ndarray:
    """A gently tilted plane, so the test is not accidentally flat-ground only."""

    rows, cols = np.indices((size, size), dtype=np.float64)
    return 1000.0 + rows * 0.05 + cols * 0.02


def _placed_material_scene(
    *,
    size: int = 200,
    datum_offset_m: float = 2.5,
    noise_sigma_m: float = 0.10,
    seed: int = 20260802,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Build an early/late pair with two known covers and a known datum shift.

    This mirrors the real situation: the two surfaces disagree by a constant
    vertical bias that has nothing to do with placed material, both carry noise,
    and only a small fraction of the scene actually changed.
    """

    rng = np.random.default_rng(seed)
    early = _baseline_surface(size)

    shallow = np.zeros((size, size), dtype=bool)
    shallow[40:70, 40:70] = True
    deep = np.zeros((size, size), dtype=bool)
    deep[120:150, 120:150] = True

    placed = np.zeros((size, size), dtype=np.float64)
    placed[shallow] = 0.70
    placed[deep] = 1.00

    late = early + placed + datum_offset_m
    early = early + rng.normal(0.0, noise_sigma_m, early.shape)
    late = late + rng.normal(0.0, noise_sigma_m, late.shape)
    return early, late, {"shallow": shallow, "deep": deep}


class TestNmad:
    def test_matches_std_for_normal_data(self) -> None:
        rng = np.random.default_rng(7)
        values = rng.normal(0.0, 2.0, 200_000)
        assert nmad(values) == pytest.approx(2.0, abs=0.05)

    def test_ignores_non_finite_values(self) -> None:
        values = np.array([1.0, 2.0, 3.0, np.nan, np.inf])
        assert nmad(values) == pytest.approx(nmad(np.array([1.0, 2.0, 3.0])))

    def test_empty_input_returns_zero(self) -> None:
        assert nmad(np.array([])) == 0.0

    def test_is_not_dragged_by_outliers(self) -> None:
        rng = np.random.default_rng(11)
        values = rng.normal(0.0, 1.0, 10_000)
        contaminated = np.concatenate([values, np.full(500, 500.0)])
        assert nmad(contaminated) == pytest.approx(nmad(values), abs=0.1)
        # The standard deviation, by contrast, is destroyed by the same input.
        assert np.std(contaminated) > 10.0


class TestStableGroundSelection:
    def test_excludes_changed_ground_from_the_datum_estimate(self) -> None:
        delta = np.zeros((100, 100), dtype=np.float64)
        delta[10:20, 10:20] = 5.0
        valid = np.ones_like(delta, dtype=bool)

        stable = select_stable_mask(delta, valid_mask=valid)

        assert not stable[10:20, 10:20].any()
        assert stable[50:60, 50:60].all()

    def test_slope_filter_drops_steep_ground(self) -> None:
        delta = np.zeros((50, 50), dtype=np.float64)
        valid = np.ones_like(delta, dtype=bool)
        slope = np.zeros_like(delta)
        slope[:10, :] = 40.0

        stable = select_stable_mask(delta, valid_mask=valid, slope_deg=slope, max_slope_deg=15.0)

        assert not stable[:10, :].any()
        assert stable[10:, :].all()

    def test_offset_is_the_median_of_stable_ground(self) -> None:
        delta = np.full((100, 100), 1.25, dtype=np.float64)
        delta[0:10, 0:10] = 9.0
        valid = np.ones_like(delta, dtype=bool)

        stats, _ = estimate_stable_ground(delta, valid_mask=valid)

        assert stats.offset_m == pytest.approx(1.25, abs=1e-9)

    def test_rejects_mismatched_shapes(self) -> None:
        with pytest.raises(CoregistrationError):
            select_stable_mask(np.zeros((10, 10)), valid_mask=np.ones((5, 5), dtype=bool))

    def test_noiseless_input_still_rejects_changed_ground(self) -> None:
        # Regression: with a perfectly noiseless difference the robust spread is
        # exactly zero. An earlier version treated that as "nothing to reject"
        # and accepted the changed block as stable ground, which would have
        # folded real placed material straight into the datum estimate.
        delta = np.zeros((100, 100), dtype=np.float64)
        delta[10:20, 10:20] = 5.0
        valid = np.ones_like(delta, dtype=bool)

        stable = select_stable_mask(delta, valid_mask=valid)
        stats, _ = estimate_stable_ground(delta, valid_mask=valid)

        assert not stable[10:20, 10:20].any()
        assert stable.sum() == 100 * 100 - 10 * 10
        assert stats.offset_m == pytest.approx(0.0)

    def test_noiseless_input_with_a_nonzero_datum_offset(self) -> None:
        delta = np.full((100, 100), -3.5, dtype=np.float64)
        delta[0:15, 0:15] = 2.0
        valid = np.ones_like(delta, dtype=bool)

        stats, stable = estimate_stable_ground(delta, valid_mask=valid)

        assert not stable[0:15, 0:15].any()
        assert stats.offset_m == pytest.approx(-3.5)


class TestCoregistration:
    def test_removes_a_known_synthetic_datum_offset(self) -> None:
        early, late, _ = _placed_material_scene(datum_offset_m=2.5)

        result = coregister_elevation_pair(early, late, nodata=NODATA)

        assert result.stats.offset_m == pytest.approx(2.5, abs=0.02)

    def test_recovers_the_pair_noise_floor(self) -> None:
        # Two surfaces each carrying sigma=0.10 differ with sigma=0.10*sqrt(2).
        early, late, _ = _placed_material_scene(noise_sigma_m=0.10)

        result = coregister_elevation_pair(early, late, nodata=NODATA)

        assert result.stats.sigma_m == pytest.approx(0.10 * np.sqrt(2.0), abs=0.01)

    def test_unchanged_ground_differences_to_zero_after_correction(self) -> None:
        early, late, regions = _placed_material_scene()
        changed = regions["shallow"] | regions["deep"]

        result = coregister_elevation_pair(early, late, nodata=NODATA)

        unchanged = result.delta_m[~changed]
        assert float(np.median(unchanged)) == pytest.approx(0.0, abs=0.01)

    def test_placed_material_survives_the_correction(self) -> None:
        early, late, regions = _placed_material_scene()

        result = coregister_elevation_pair(early, late, nodata=NODATA)

        assert float(np.mean(result.delta_m[regions["shallow"]])) == pytest.approx(0.70, abs=0.03)
        assert float(np.mean(result.delta_m[regions["deep"]])) == pytest.approx(1.00, abs=0.03)

    def test_honours_nodata_in_either_epoch(self) -> None:
        early, late, _ = _placed_material_scene()
        early[0:20, :] = NODATA
        late[:, 0:20] = NODATA

        result = coregister_elevation_pair(early, late, nodata=NODATA)

        assert not result.valid_mask[0:20, :].any()
        assert not result.valid_mask[:, 0:20].any()
        assert np.isnan(result.delta_m[0:20, :]).all()

    def test_refuses_when_stable_ground_is_too_small(self) -> None:
        early, late, _ = _placed_material_scene(size=20)

        with pytest.raises(CoregistrationError, match="insufficient stable ground"):
            coregister_elevation_pair(early, late, nodata=NODATA, min_stable_pixels=100_000)

    def test_refuses_when_the_epochs_never_overlap(self) -> None:
        early = np.full((50, 50), NODATA, dtype=np.float64)
        late = np.zeros((50, 50), dtype=np.float64)

        with pytest.raises(CoregistrationError, match="no pixel has valid data"):
            coregister_elevation_pair(early, late, nodata=NODATA)

    def test_rejects_mismatched_grids(self) -> None:
        with pytest.raises(CoregistrationError, match="share one grid shape"):
            coregister_elevation_pair(np.zeros((10, 10)), np.zeros((10, 12)), nodata=NODATA)

    def test_flags_a_large_datum_offset(self) -> None:
        early, late, _ = _placed_material_scene(datum_offset_m=25.0)

        result = coregister_elevation_pair(early, late, nodata=NODATA)

        assert "large_vertical_datum_offset_removed" in result.warnings


class TestSharedDataDetection:
    """Two surfaces that agree exactly are not two measurements.

    Found on real data. Copernicus GLO-30 fills voids from other sources, and
    over one real site every pixel was filled rather than measured, with 37.7%
    of the difference against NASADEM exactly zero. The reported noise floor
    was 0.41 m and looked excellent; it was an artefact of comparing SRTM with
    itself, and real change in the shared area could not have shown up at all.
    """

    def test_identical_surfaces_are_refused(self) -> None:
        rng = np.random.default_rng(1)
        surface = 100.0 + rng.normal(0.0, 1.0, (200, 200))

        with pytest.raises(CoregistrationError, match="not two independent measurements"):
            coregister_elevation_pair(surface, surface.copy(), nodata=NODATA)

    def test_partly_shared_surfaces_are_refused(self) -> None:
        early, late, _ = _placed_material_scene()
        # Copy a third of the early surface into the late one, as void filling
        # from a common ancestor would.
        late[:, :67] = early[:, :67]

        with pytest.raises(CoregistrationError, match="identical over"):
            coregister_elevation_pair(early, late, nodata=NODATA)

    def test_the_error_names_the_diagnostic(self) -> None:
        rng = np.random.default_rng(2)
        surface = 50.0 + rng.normal(0.0, 0.5, (150, 150))

        with pytest.raises(CoregistrationError, match="diagnose_elevation_pair"):
            coregister_elevation_pair(surface, surface.copy(), nodata=NODATA)

    def test_a_small_shared_patch_only_warns(self) -> None:
        early, late, _ = _placed_material_scene()
        late[:, :16] = early[:, :16]  # 8% of the scene

        result = coregister_elevation_pair(early, late, nodata=NODATA)

        assert "some_shared_data_between_epochs" in result.warnings
        assert 0.05 < result.shared_data_fraction < 0.20

    def test_independent_surfaces_report_no_shared_data(self) -> None:
        early, late, _ = _placed_material_scene()

        result = coregister_elevation_pair(early, late, nodata=NODATA)

        assert result.shared_data_fraction < 0.01
        assert "some_shared_data_between_epochs" not in result.warnings

    def test_catches_a_copy_shifted_to_another_vertical_datum(self) -> None:
        # The same data republished against a different datum differs by a
        # constant, not by zero. A zero-anchored test sails straight past it,
        # which is why the check is anchored on the median instead.
        rng = np.random.default_rng(3)
        early = 100.0 + rng.normal(0.0, 0.5, (200, 200))
        late = early.copy() + 5.0

        with pytest.raises(CoregistrationError, match="not two independent measurements"):
            coregister_elevation_pair(early, late, nodata=NODATA)

    def test_catches_a_verbatim_copy(self) -> None:
        # The real observed case: void filling copies values across unchanged,
        # so the difference is exactly zero.
        rng = np.random.default_rng(4)
        surface = 40.0 + rng.normal(0.0, 0.5, (200, 200))
        valid = np.ones(surface.shape, dtype=bool)

        assert shared_data_fraction(surface - surface, valid_mask=valid) == pytest.approx(1.0)

    def test_catches_a_partial_copy_hiding_behind_a_datum_offset(self) -> None:
        # The hardest case, and the one that broke two earlier versions of this
        # check. A third of the area is copied so its difference is zero, while
        # the genuine majority sits at the datum offset. Anchoring on zero or on
        # the median each miss it; a spike at any single value does not.
        rng = np.random.default_rng(7)
        delta = 2.5 + rng.normal(0.0, 0.3, (300, 300))
        delta[:100, :] = 0.0
        valid = np.ones(delta.shape, dtype=bool)

        assert shared_data_fraction(delta, valid_mask=valid) == pytest.approx(1 / 3, abs=0.01)

    def test_independent_data_almost_never_lands_on_one_value(self) -> None:
        rng = np.random.default_rng(5)
        delta = rng.normal(0.0, 1.0, (300, 300))
        valid = np.ones(delta.shape, dtype=bool)

        assert shared_data_fraction(delta, valid_mask=valid) < 0.001

    def test_matches_the_share_observed_on_real_data(self) -> None:
        # Reproduces the live result that prompted this guard: 37.7% of the
        # NASADEM/Copernicus difference sat exactly at zero over a real site.
        rng = np.random.default_rng(6)
        delta = rng.normal(0.0, 1.0, (1000, 1000))
        delta[:377, :] = 0.0
        valid = np.ones(delta.shape, dtype=bool)

        fraction = shared_data_fraction(delta, valid_mask=valid)

        assert fraction == pytest.approx(0.377, abs=0.01)
        assert fraction >= 0.20  # above the refusal threshold


class TestCorrelatedUncertainty:
    def test_no_averaging_benefit_below_one_correlation_area(self) -> None:
        sigma = correlated_mean_uncertainty(
            sigma_stable_m=0.14,
            area_m2=100.0,
            correlation_length_m=200.0,
        )
        assert sigma == pytest.approx(0.14)

    def test_large_areas_average_down(self) -> None:
        small = correlated_mean_uncertainty(
            sigma_stable_m=0.14, area_m2=50_000.0, correlation_length_m=200.0
        )
        large = correlated_mean_uncertainty(
            sigma_stable_m=0.14, area_m2=500_000.0, correlation_length_m=200.0
        )
        assert large < small < 0.14

    def test_never_beats_independent_pixel_averaging_by_accident(self) -> None:
        # The correlated estimate must stay well above the naive 1/sqrt(N) value
        # that treating pixels as independent would produce.
        area = 500_000.0
        pixels = area / PIXEL_AREA_M2
        naive = 0.14 / np.sqrt(pixels)
        correlated = correlated_mean_uncertainty(
            sigma_stable_m=0.14, area_m2=area, correlation_length_m=200.0
        )
        assert correlated > naive * 5

    def test_rejects_invalid_configuration(self) -> None:
        with pytest.raises(ThicknessError):
            correlated_mean_uncertainty(sigma_stable_m=0.1, area_m2=0.0)
        with pytest.raises(ThicknessError):
            correlated_mean_uncertainty(
                sigma_stable_m=0.1, area_m2=10.0, correlation_length_m=0.0
            )


class TestPolygonThickness:
    def _measure(self, region: np.ndarray, delta: np.ndarray, zone_id: str, sigma: float):
        return measure_polygon_thickness(
            delta,
            region,
            zone_id=zone_id,
            sigma_stable_m=sigma,
            pixel_area_m2=PIXEL_AREA_M2,
        )

    def test_measures_the_two_known_covers(self) -> None:
        early, late, regions = _placed_material_scene()
        result = coregister_elevation_pair(early, late, nodata=NODATA)

        shallow = self._measure(regions["shallow"], result.delta_m, "shallow", result.stats.sigma_m)
        deep = self._measure(regions["deep"], result.delta_m, "deep", result.stats.sigma_m)

        assert shallow.measurable
        assert deep.measurable
        assert shallow.mean_change_m == pytest.approx(0.70, abs=0.05)
        assert deep.mean_change_m == pytest.approx(1.00, abs=0.05)

    def test_reported_interval_brackets_the_truth(self) -> None:
        early, late, regions = _placed_material_scene()
        result = coregister_elevation_pair(early, late, nodata=NODATA)

        shallow = self._measure(regions["shallow"], result.delta_m, "shallow", result.stats.sigma_m)
        deep = self._measure(regions["deep"], result.delta_m, "deep", result.stats.sigma_m)

        shallow_range = shallow.depth_range()
        deep_range = deep.depth_range()
        assert shallow_range is not None and deep_range is not None
        assert shallow_range.minimum_m <= 0.70 <= shallow_range.maximum_m
        assert deep_range.minimum_m <= 1.00 <= deep_range.maximum_m

    def test_ordering_is_preserved(self) -> None:
        early, late, regions = _placed_material_scene()
        result = coregister_elevation_pair(early, late, nodata=NODATA)

        shallow = self._measure(regions["shallow"], result.delta_m, "shallow", result.stats.sigma_m)
        deep = self._measure(regions["deep"], result.delta_m, "deep", result.stats.sigma_m)

        assert deep.mean_change_m > shallow.mean_change_m

    def test_abstains_on_unchanged_ground(self) -> None:
        early, late, regions = _placed_material_scene()
        result = coregister_elevation_pair(early, late, nodata=NODATA)
        untouched = np.zeros(result.delta_m.shape, dtype=bool)
        untouched[170:195, 20:45] = True
        assert not (untouched & (regions["shallow"] | regions["deep"])).any()

        measured = self._measure(untouched, result.delta_m, "control", result.stats.sigma_m)

        assert not measured.measurable
        assert measured.depth_range() is None
        assert "change_within_noise_floor" in measured.warnings

    def test_flags_removed_material_instead_of_reporting_depth(self) -> None:
        delta = np.full((100, 100), -1.5, dtype=np.float64)
        region = np.zeros_like(delta, dtype=bool)
        region[10:60, 10:60] = True

        measured = self._measure(region, delta, "excavation", 0.10)

        assert measured.is_significant
        assert not measured.is_accumulation
        assert measured.depth_range() is None
        assert "material_removed_not_added" in measured.warnings

    def test_abstains_when_too_few_pixels(self) -> None:
        delta = np.full((100, 100), 2.0, dtype=np.float64)
        region = np.zeros_like(delta, dtype=bool)
        region[0:2, 0:2] = True

        measured = self._measure(region, delta, "tiny", 0.10)

        assert not measured.measurable
        assert "insufficient_valid_pixels" in measured.warnings

    def test_ignores_nan_pixels_inside_the_polygon(self) -> None:
        delta = np.full((100, 100), 0.80, dtype=np.float64)
        delta[0:50, 0:25] = np.nan
        region = np.zeros_like(delta, dtype=bool)
        region[0:50, 0:50] = True

        measured = self._measure(region, delta, "partial", 0.05)

        assert measured.pixel_count == 50 * 25
        assert measured.mean_change_m == pytest.approx(0.80)

    def test_requires_a_zone_id(self) -> None:
        with pytest.raises(ThicknessError):
            measure_polygon_thickness(
                np.zeros((10, 10)),
                np.ones((10, 10), dtype=bool),
                zone_id="  ",
                sigma_stable_m=0.1,
                pixel_area_m2=PIXEL_AREA_M2,
            )


class TestSignificantChangeMask:
    def test_finds_the_covered_ground_without_a_supplied_outline(self) -> None:
        early, late, regions = _placed_material_scene()
        result = coregister_elevation_pair(early, late, nodata=NODATA)

        detected = significant_change_mask(
            result.delta_m, sigma_stable_m=result.stats.sigma_m
        )

        truth = regions["shallow"] | regions["deep"]
        # Nearly all genuinely covered pixels are found ...
        assert detected[truth].mean() > 0.95
        # ... and almost none of the untouched ground is falsely flagged.
        assert detected[~truth].mean() < 0.05

    def test_threshold_scales_with_the_noise_floor(self) -> None:
        delta = np.full((50, 50), 0.30, dtype=np.float64)

        assert significant_change_mask(delta, sigma_stable_m=0.05).all()
        assert not significant_change_mask(delta, sigma_stable_m=0.50).any()


def test_default_correlation_length_is_conservative() -> None:
    # A default that is too short would silently narrow every published interval.
    assert DEFAULT_CORRELATION_LENGTH_M >= 100.0
