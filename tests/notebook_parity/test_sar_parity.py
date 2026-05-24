from __future__ import annotations

from app.pipeline.stages.grid import build_run_grid
from app.pipeline.stages.sar_rtc import (
    DEFAULT_END,
    DEFAULT_START,
    build_final_radar_image,
    create_ee_radar_cube_fetcher,
    fc_time_ids,
    finalize_for_sample,
    per_image_products_db,
    pick_best_track,
    select_pairs,
    to_grid_radar,
)


def test_sar_parity_uses_notebook_collection_pair_and_sampling_flow(monkeypatch) -> None:
    grid_spec = build_run_grid(35.59499, 36.12694)
    calls: list[tuple[str, object]] = []

    class FakeNumber:
        def __init__(self, value):
            self.value = value

        def getInfo(self):
            return self.value

    class FakeString:
        def __init__(self, value):
            self.value = value

    class FakeFeature:
        def __init__(self, _geometry, properties):
            self.properties = properties

        def get(self, key):
            return self.properties[key]

    class FakeFeatureCollection:
        def __init__(self, features):
            self.features = list(features)

        def sort(self, key, descending=False):
            reverse = bool(descending)
            return FakeFeatureCollection(
                sorted(
                    self.features,
                    key=lambda feature: feature.properties[key].value
                    if hasattr(feature.properties[key], "value")
                    else feature.properties[key],
                    reverse=reverse,
                )
            )

        def first(self):
            return self.features[0]

        def getInfo(self):
            return {
                "features": [
                    {"properties": {"ms": feature.properties["ms"].value, "id": feature.properties["id"].value}}
                    for feature in self.features
                ]
            }

    class FakeList:
        def __init__(self, values):
            self.values = list(values)

        def distinct(self):
            seen = []
            for value in self.values:
                raw = value.value if hasattr(value, "value") else value
                if raw not in seen:
                    seen.append(raw)
            return FakeList(seen)

        def map(self, fn):
            return [fn(value) for value in self.values]

    class FakeFilter:
        @staticmethod
        def eq(name, value):
            calls.append(("eq", (name, value)))
            return ("eq", name, value)

        @staticmethod
        def listContains(name, value):
            calls.append(("listContains", (name, value)))
            return ("listContains", name, value)

    class FakeSampleResult:
        def getInfo(self):
            calls.append(("getInfo", None))
            return {"properties": {band: [[2.0] * 320 for _ in range(320)] for band in ["VV_dB", "VH_dB", "angle"]}}

    class FakeImage:
        def __init__(self, image_id=None, properties=None, bands=None):
            self.image_id = image_id
            self.properties = properties or {}
            self.bands = bands or ["VV", "VH", "angle"]

        def select(self, bands):
            calls.append(("select", bands))
            return FakeImage(self.image_id, dict(self.properties), list(bands))

        def clip(self, region):
            calls.append(("clip", region))
            return self

        def rename(self, name):
            calls.append(("rename", name))
            return FakeImage(self.image_id, dict(self.properties), [name])

        def toFloat(self):
            calls.append(("toFloat", None))
            return self

        def reproject(self, *, crs, crsTransform):
            calls.append(("reproject", {"crs": crs, "crsTransform": crsTransform}))
            return self

        def unmask(self, nodata):
            calls.append(("unmask", nodata))
            return self

        def gt(self, value):
            calls.append(("gt", value))
            return self

        def And(self, other):
            calls.append(("And", other))
            return self

        def lt(self, value):
            calls.append(("lt", value))
            return self

        def updateMask(self, mask):
            calls.append(("updateMask", mask))
            return self

        def divide(self, value):
            calls.append(("divide", value))
            return self

        def pow(self, value):
            calls.append(("pow", value))
            return self

        def max(self, value):
            calls.append(("max", value))
            return self

        def log10(self):
            calls.append(("log10", None))
            return self

        def multiply(self, value):
            calls.append(("multiply", value))
            return self

        def reduceNeighborhood(self, reducer, kernel):
            calls.append(("reduceNeighborhood", {"reducer": reducer, "kernel": kernel}))
            return self

        def subtract(self, value):
            calls.append(("subtract", value))
            return self

        def clamp(self, low, high):
            calls.append(("clamp", (low, high)))
            return self

        def add(self, value):
            calls.append(("add", value))
            return self

        def gte(self, value):
            calls.append(("gte", value))
            return self

        def lte(self, value):
            calls.append(("lte", value))
            return self

        def where(self, test, value):
            calls.append(("where", (test, value)))
            return self

        def sampleRectangle(self, *, region, defaultValue):
            calls.append(("sampleRectangle", {"region": region, "defaultValue": defaultValue}))
            return FakeSampleResult()

        def get(self, key):
            return self.properties[key]

        def id(self):
            return self.image_id

    class FakeImageCollection:
        def __init__(self, dataset_or_images):
            self.dataset = dataset_or_images if isinstance(dataset_or_images, str) else None
            self.images = (
                list(dataset_or_images)
                if isinstance(dataset_or_images, list)
                else [
                    FakeImage(
                        "ASC_1",
                        {
                            "system:time_start": FakeNumber(1000),
                            "relativeOrbitNumber_start": 7,
                            "orbitProperties_pass": "ASCENDING",
                        },
                    ),
                    FakeImage(
                        "ASC_2",
                        {
                            "system:time_start": FakeNumber(2000),
                            "relativeOrbitNumber_start": 7,
                            "orbitProperties_pass": "ASCENDING",
                        },
                    ),
                    FakeImage(
                        "DESC_1",
                        {
                            "system:time_start": FakeNumber(1100),
                            "relativeOrbitNumber_start": 11,
                            "orbitProperties_pass": "DESCENDING",
                        },
                    ),
                    FakeImage(
                        "DESC_2",
                        {
                            "system:time_start": FakeNumber(2100),
                            "relativeOrbitNumber_start": 11,
                            "orbitProperties_pass": "DESCENDING",
                        },
                    ),
                ]
            )
            if self.dataset:
                calls.append(("ImageCollection", self.dataset))

        def filterBounds(self, region):
            calls.append(("filterBounds", region))
            return self

        def filterDate(self, start, end):
            calls.append(("filterDate", (start, end)))
            return self

        def filter(self, predicate):
            calls.append(("filter", predicate))
            if predicate[0] != "eq":
                return self
            name, value = predicate[1], predicate[2]
            if all(name not in image.properties for image in self.images):
                return self
            return FakeImageCollection([image for image in self.images if image.properties.get(name) == value])

        def select(self, bands):
            calls.append(("collection_select", bands))
            return self

        def aggregate_array(self, name):
            return FakeList([image.properties[name] for image in self.images])

        def size(self):
            return FakeNumber(len(self.images))

        def map(self, fn):
            return [fn(image) for image in self.images]

        def median(self):
            calls.append(("median", None))
            return FakeImage("median", {}, ["VV_dB", "VH_dB", "angle"])

    class FakeGeometry:
        @staticmethod
        def Rectangle(coords, crs, geodesic):
            calls.append(("Rectangle", {"coords": coords, "crs": crs, "geodesic": geodesic}))
            return "grid-region"

    class FakeKernel:
        @staticmethod
        def square(radius, units, normalize):
            value = ("square", radius, units, normalize)
            calls.append(("Kernel.square", value))
            return value

    class FakeReducer:
        @staticmethod
        def mean():
            calls.append(("Reducer.mean", None))
            return "mean"

        @staticmethod
        def variance():
            calls.append(("Reducer.variance", None))
            return "variance"

        @staticmethod
        def stdDev():
            calls.append(("Reducer.stdDev", None))
            return "stdDev"

    def fake_image_constructor(value):
        if isinstance(value, FakeImage):
            return value
        if isinstance(value, str) and value.startswith("COPERNICUS/S1_GRD/"):
            image_id = value.split("/")[-1]
            orbit = "ASCENDING" if image_id.startswith("ASC") else "DESCENDING"
            track = 7 if orbit == "ASCENDING" else 11
            ms = 1000 if image_id.endswith("1") else 2000
            return FakeImage(
                image_id,
                {
                    "system:time_start": FakeNumber(ms),
                    "relativeOrbitNumber_start": track,
                    "orbitProperties_pass": orbit,
                },
            )
        return FakeImage()

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.initialize_ee_session", lambda settings: calls.append(("init", settings.bind_host)))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Filter", FakeFilter)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.ImageCollection", FakeImageCollection)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Image", fake_image_constructor)
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc.ee.Image.constant",
        staticmethod(lambda value: calls.append(("constant", value)) or FakeImage()),
        raising=False,
    )
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Geometry", FakeGeometry)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Kernel", FakeKernel)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Reducer", FakeReducer)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.List", lambda values: values if isinstance(values, FakeList) else FakeList(values))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Number", lambda value: value if isinstance(value, FakeNumber) else FakeNumber(value))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.String", lambda value: value if isinstance(value, FakeString) else FakeString(value))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Feature", FakeFeature)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.FeatureCollection", FakeFeatureCollection)
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc.fc_time_ids",
        lambda collection: [
            {"ms": 1000, "id": "ASC_1"},
            {"ms": 2000, "id": "ASC_2"},
        ]
        if any(image.properties.get("orbitProperties_pass") == "ASCENDING" for image in collection.images)
        else [
            {"ms": 1100, "id": "DESC_1"},
            {"ms": 2100, "id": "DESC_2"},
        ],
    )
    monkeypatch.setattr(
        "app.pipeline.stages.sar_rtc.ee.Image.cat",
        staticmethod(lambda images: calls.append(("cat", len(images))) or FakeImage("cat", {}, ["VV_dB", "VH_dB", "angle"])),
        raising=False,
    )

    final_radar, pairs = build_final_radar_image(grid_spec, start_date=DEFAULT_START, end_date=DEFAULT_END)
    assert len(pairs) == 2

    grid_image = to_grid_radar(final_radar, grid_spec)
    sampled_image = finalize_for_sample(grid_image, grid_spec)
    assert per_image_products_db(fake_image_constructor("COPERNICUS/S1_GRD/ASC_1")) is not None

    fetcher = create_ee_radar_cube_fetcher(_settings(), grid_spec, start_date=DEFAULT_START, end_date=DEFAULT_END)
    cube = fetcher(grid_spec=grid_spec)

    assert cube.shape == (640, 640, 3)
    assert ("ImageCollection", "COPERNICUS/S1_GRD") in calls
    assert ("filterBounds", "grid-region") in calls
    assert ("filterDate", (DEFAULT_START, DEFAULT_END)) in calls
    assert ("eq", ("instrumentMode", "IW")) in calls
    assert ("eq", ("resolution_meters", 10)) in calls
    assert ("listContains", ("transmitterReceiverPolarisation", "VV")) in calls
    assert ("listContains", ("transmitterReceiverPolarisation", "VH")) in calls
    assert ("collection_select", ["VV", "VH", "angle"]) in calls
    assert ("eq", ("orbitProperties_pass", "ASCENDING")) in calls
    assert ("eq", ("orbitProperties_pass", "DESCENDING")) in calls
    relative_track_eqs = [value for name, value in calls if name == "eq" and value[0] == "relativeOrbitNumber_start"]
    assert len(relative_track_eqs) >= 2
    assert ("median", None) in calls
    assert ("reproject", {"crs": grid_spec.crs, "crsTransform": list(grid_spec.transform)}) in calls
    assert len([name for name, _value in calls if name == "sampleRectangle"]) == 4
    assert sampled_image is not None


def test_sar_parity_select_pairs_behavior() -> None:
    pairs = select_pairs(
        [{"ms": 1000, "id": "ASC_1"}, {"ms": 2000, "id": "ASC_2"}],
        [{"ms": 1100, "id": "DESC_1"}, {"ms": 2100, "id": "DESC_2"}],
    )

    assert len(pairs) == 2
    assert pairs[0].dt_ms <= pairs[1].dt_ms


def test_sar_parity_fc_time_ids_extracts_sorted_pairs(monkeypatch) -> None:
    class FakeNumber:
        def __init__(self, value):
            self.value = value

    class FakeString:
        def __init__(self, value):
            self.value = value

    class FakeFeature:
        def __init__(self, _geometry, properties):
            self.properties = properties

    class FakeFeatureCollection:
        def __init__(self, features):
            self.features = list(features)

        def sort(self, _key):
            return self

        def getInfo(self):
            return {
                "features": [
                    {"properties": {"ms": feature.properties["ms"].value, "id": feature.properties["id"].value}}
                    for feature in self.features
                ]
            }

    class FakeImage:
        def __init__(self, image_id, ms):
            self._id = image_id
            self._ms = ms

        def get(self, key):
            assert key == "system:time_start"
            return FakeNumber(self._ms)

        def id(self):
            return self._id

    class FakeCollection:
        def __init__(self, images):
            self.images = images

        def map(self, fn):
            return [fn(image) for image in self.images]

    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Image", lambda image: image)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Number", lambda value: value if isinstance(value, FakeNumber) else FakeNumber(value))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.String", lambda value: value if isinstance(value, FakeString) else FakeString(value))
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.Feature", FakeFeature)
    monkeypatch.setattr("app.pipeline.stages.sar_rtc.ee.FeatureCollection", FakeFeatureCollection)

    result = fc_time_ids(FakeCollection([FakeImage("ASC_1", 1000), FakeImage("ASC_2", 2000)]))

    assert result == [
        {"ms": 1000, "id": "ASC_1"},
        {"ms": 2000, "id": "ASC_2"},
    ]


def _settings():
    from app.config import Settings

    return Settings()
