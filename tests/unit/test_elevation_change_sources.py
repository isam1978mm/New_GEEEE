from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.pipeline.elevation_change.sources import (
    ASSET_IMAGE,
    ASSET_IMAGE_COLLECTION,
    COVERAGE_GLOBAL,
    COVERAGE_UNITED_STATES,
    ELEVATION_SOURCES,
    SOURCES_BY_KEY,
    ElevationPair,
    ElevationSourceError,
    build_ee_elevation_image,
    candidate_epochs,
    select_source_pair,
    sources_for_coverage,
)


class TestCatalogue:
    def test_every_source_key_is_unique(self) -> None:
        keys = [source.key for source in ELEVATION_SOURCES]
        assert len(set(keys)) == len(keys)
        assert set(SOURCES_BY_KEY) == set(keys)

    def test_every_source_is_open_data_needing_no_correspondence(self) -> None:
        # The constraint that started this work: no site, no company, no person.
        # Every asset must be a public Earth Engine catalogue id.
        for source in ELEVATION_SOURCES:
            assert source.asset_id
            assert not source.asset_id.startswith("users/")
            assert not source.asset_id.startswith("projects/earthengine-legacy/assets/users/")

    def test_asset_kinds_are_supported(self) -> None:
        for source in ELEVATION_SOURCES:
            assert source.asset_kind in {ASSET_IMAGE, ASSET_IMAGE_COLLECTION}

    def test_lidar_is_the_only_source_fine_enough_for_a_thin_cover(self) -> None:
        fine = [
            source
            for source in ELEVATION_SOURCES
            if source.nominal_vertical_sigma_m <= 0.2
        ]
        assert [source.key for source in fine] == ["usgs_3dep_1m"]

    def test_global_sources_cannot_resolve_a_one_metre_cover(self) -> None:
        # Stated plainly so nobody later assumes global coverage means global
        # capability. A 30 m DEM pair cannot see a metre of soil.
        pair = select_source_pair(coverage=COVERAGE_GLOBAL)
        assert pair.minimum_detectable_thickness_m > 1.0


class TestCoverageTiers:
    def test_united_states_may_use_every_source(self) -> None:
        assert len(sources_for_coverage(COVERAGE_UNITED_STATES)) == len(ELEVATION_SOURCES)

    def test_global_excludes_united_states_only_sources(self) -> None:
        keys = {source.key for source in sources_for_coverage(COVERAGE_GLOBAL)}
        assert "usgs_3dep_1m" not in keys
        assert "usgs_ned" not in keys
        assert "copernicus_glo30" in keys

    def test_rejects_an_unknown_tier(self) -> None:
        with pytest.raises(ElevationSourceError, match="unsupported coverage"):
            sources_for_coverage("mars")


class TestSelectSourcePair:
    def test_pairs_two_lidar_vintages_in_the_united_states(self) -> None:
        # Regression on a real design flaw: pairing lidar against a coarse legacy
        # baseline gave a 2.9 m detection floor, which cannot see a soil cover at
        # all. A pair is only as good as its worse half.
        pair = select_source_pair(coverage=COVERAGE_UNITED_STATES)

        assert pair.early.source.key == "usgs_3dep_1m"
        assert pair.late.source.key == "usgs_3dep_1m"
        assert pair.same_source is True
        assert pair.early.start_year < pair.late.start_year
        assert pair.minimum_detectable_thickness_m < 0.5

    def test_lidar_pair_can_see_a_typical_soil_cover(self) -> None:
        pair = select_source_pair(coverage=COVERAGE_UNITED_STATES)
        # The cover depths this project actually cares about are 0.6-1.0 m.
        assert pair.minimum_detectable_thickness_m < 0.6

    def test_same_source_pairing_warns_that_overlap_is_not_guaranteed(self) -> None:
        pair = select_source_pair(coverage=COVERAGE_UNITED_STATES)
        assert "requires_two_overlapping_vintages_at_this_location" in pair.warnings

    def test_united_states_beats_global_by_an_order_of_magnitude(self) -> None:
        united_states = select_source_pair(coverage=COVERAGE_UNITED_STATES)
        global_tier = select_source_pair(coverage=COVERAGE_GLOBAL)
        assert (
            united_states.minimum_detectable_thickness_m * 10
            < global_tier.minimum_detectable_thickness_m
        )

    def test_late_epoch_follows_the_early_epoch(self) -> None:
        for coverage in (COVERAGE_UNITED_STATES, COVERAGE_GLOBAL):
            pair = select_source_pair(coverage=coverage)
            assert pair.epoch_separation_years > 0

    def test_warns_when_the_target_is_below_the_detection_floor(self) -> None:
        pair = select_source_pair(coverage=COVERAGE_GLOBAL, target_thickness_m=0.7)
        assert "target_thickness_below_detection_floor" in pair.warnings

    def test_does_not_warn_when_lidar_can_see_the_target(self) -> None:
        pair = select_source_pair(coverage=COVERAGE_UNITED_STATES, target_thickness_m=0.7)
        assert "target_thickness_below_detection_floor" not in pair.warnings

    def test_warns_about_coarse_resolution(self) -> None:
        pair = select_source_pair(coverage=COVERAGE_GLOBAL)
        assert "coarse_resolution_small_features_unresolvable" in pair.warnings

    def test_honours_a_restricted_availability_list(self) -> None:
        pair = select_source_pair(
            coverage=COVERAGE_UNITED_STATES,
            available_keys=["nasadem", "copernicus_glo30"],
        )
        assert {pair.early.source.key, pair.late.source.key} == {
            "nasadem",
            "copernicus_glo30",
        }

    def test_a_lone_multi_vintage_source_can_still_form_a_pair(self) -> None:
        pair = select_source_pair(
            coverage=COVERAGE_UNITED_STATES, available_keys=["usgs_3dep_1m"]
        )
        assert pair.same_source is True

    def test_refuses_when_a_lone_source_has_only_one_epoch(self) -> None:
        with pytest.raises(ElevationSourceError, match="at least two elevation epochs"):
            select_source_pair(
                coverage=COVERAGE_UNITED_STATES, available_keys=["nasadem"]
            )

    def test_refuses_when_no_pair_has_enough_epoch_separation(self) -> None:
        with pytest.raises(ElevationSourceError, match="epoch separation"):
            select_source_pair(
                coverage=COVERAGE_UNITED_STATES,
                min_epoch_separation_years=500.0,
            )


class TestElevationPairArithmetic:
    def _pair(self, early_key: str, late_key: str) -> ElevationPair:
        return ElevationPair(
            early=candidate_epochs(SOURCES_BY_KEY[early_key])[0],
            late=candidate_epochs(SOURCES_BY_KEY[late_key])[-1],
        )

    def test_expected_sigma_combines_both_sources_in_quadrature(self) -> None:
        pair = self._pair("nasadem", "copernicus_glo30")
        assert pair.expected_sigma_m == pytest.approx((3.0**2 + 2.0**2) ** 0.5)

    def test_detection_floor_scales_with_expected_sigma(self) -> None:
        pair = self._pair("nasadem", "copernicus_glo30")
        assert pair.minimum_detectable_thickness_m == pytest.approx(
            1.96 * pair.expected_sigma_m
        )

    def test_working_resolution_is_the_coarser_of_the_two(self) -> None:
        pair = self._pair("nasadem", "usgs_3dep_1m")
        assert pair.working_resolution_m == 30.0

    def test_serialises_without_losing_the_warnings(self) -> None:
        pair = select_source_pair(coverage=COVERAGE_GLOBAL, target_thickness_m=0.5)
        payload = pair.as_mapping()
        assert payload["warnings"] == list(pair.warnings)
        assert payload["early"]["asset_id"]
        assert payload["late"]["asset_id"]


class _FakeImage:
    def __init__(self, asset_id: str, *, mosaicked: bool = False) -> None:
        self.asset_id = asset_id
        self.mosaicked = mosaicked
        self.selected: str | None = None
        self.clipped: object | None = None
        self.floated = False
        self.bounds_filter: object | None = None
        self.date_filter: tuple[str, str] | None = None

    def filterBounds(self, region: object) -> "_FakeImage":  # noqa: N802
        self.bounds_filter = region
        return self

    def filterDate(self, start: str, end: str) -> "_FakeImage":  # noqa: N802
        self.date_filter = (start, end)
        return self

    def mosaic(self) -> "_FakeImage":
        mosaicked = _FakeImage(self.asset_id, mosaicked=True)
        mosaicked.bounds_filter = self.bounds_filter
        mosaicked.date_filter = self.date_filter
        return mosaicked

    def select(self, band: str) -> "_FakeImage":
        self.selected = band
        return self

    def clip(self, region: object) -> "_FakeImage":
        self.clipped = region
        return self

    def toFloat(self) -> "_FakeImage":  # noqa: N802 - Earth Engine naming
        self.floated = True
        return self


def _fake_ee() -> SimpleNamespace:
    return SimpleNamespace(
        Image=lambda asset_id: _FakeImage(asset_id),
        ImageCollection=lambda asset_id: _FakeImage(asset_id),
    )


class TestBuildEeElevationImage:
    def test_mosaics_a_collection_source(self) -> None:
        epoch = candidate_epochs(SOURCES_BY_KEY["usgs_3dep_1m"])[0]
        image = build_ee_elevation_image(epoch, region="REGION", ee_module=_fake_ee())

        assert image.mosaicked is True
        assert image.selected == epoch.source.band
        assert image.clipped == "REGION"
        assert image.floated is True

    def test_multi_vintage_source_is_filtered_to_its_epoch_window(self) -> None:
        early, late = candidate_epochs(SOURCES_BY_KEY["usgs_3dep_1m"])

        early_image = build_ee_elevation_image(early, region="R", ee_module=_fake_ee())
        late_image = build_ee_elevation_image(late, region="R", ee_module=_fake_ee())

        assert early_image.date_filter == (f"{early.start_year}-01-01", f"{early.end_year}-12-31")
        assert late_image.date_filter == (f"{late.start_year}-01-01", f"{late.end_year}-12-31")
        # Without distinct windows both halves would be the same mosaic and the
        # difference would be identically zero.
        assert early_image.date_filter != late_image.date_filter

    def test_single_vintage_collection_is_not_date_filtered(self) -> None:
        epoch = candidate_epochs(SOURCES_BY_KEY["copernicus_glo30"])[0]
        image = build_ee_elevation_image(epoch, region="R", ee_module=_fake_ee())

        assert image.date_filter is None
        assert image.mosaicked is True

    def test_does_not_mosaic_a_single_image_source(self) -> None:
        epoch = candidate_epochs(SOURCES_BY_KEY["nasadem"])[0]
        image = build_ee_elevation_image(epoch, region="REGION", ee_module=_fake_ee())

        assert image.mosaicked is False
        assert image.selected == epoch.source.band

    def test_uses_the_catalogue_asset_id_verbatim(self) -> None:
        for source in ELEVATION_SOURCES:
            for epoch in candidate_epochs(source):
                image = build_ee_elevation_image(epoch, region="R", ee_module=_fake_ee())
                assert image.asset_id == source.asset_id


class TestCandidateEpochs:
    def test_single_vintage_source_yields_one_epoch(self) -> None:
        assert len(candidate_epochs(SOURCES_BY_KEY["nasadem"])) == 1

    def test_multi_vintage_source_splits_into_two_windows(self) -> None:
        epochs = candidate_epochs(SOURCES_BY_KEY["usgs_3dep_1m"])
        assert len(epochs) == 2
        assert epochs[0].end_year == epochs[1].start_year
        assert epochs[0].midpoint_year < epochs[1].midpoint_year

    def test_multi_vintage_epochs_are_labelled_distinctly(self) -> None:
        early, late = candidate_epochs(SOURCES_BY_KEY["usgs_3dep_1m"])
        assert early.label != late.label
        assert early.label.startswith("usgs_3dep_1m@")

    def test_single_vintage_label_is_just_the_key(self) -> None:
        assert candidate_epochs(SOURCES_BY_KEY["nasadem"])[0].label == "nasadem"
