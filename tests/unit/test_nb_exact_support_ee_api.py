from __future__ import annotations

import numpy as np

import app.pipeline.stages.nb_exact_support as nb_exact_support
from app.pipeline.stages.nb_exact_support import (
    NotebookSupportInputs,
    _resolve_support_inputs,
    _speckle_filter,
)


class _FakeElement:
    pass


class _FakeEeImage:
    def __init__(self) -> None:
        self.focal_mean_call: tuple[float, str, str] | None = None
        self.copy_properties_call: tuple[object, object] | None = None
        self.element = _FakeElement()

    def focalMean(self, *, radius: float, kernelType: str, units: str):
        self.focal_mean_call = (radius, kernelType, units)
        return self

    def propertyNames(self):
        return ["system:time_start"]

    def copyProperties(self, source, properties):
        self.copy_properties_call = (source, properties)
        return self.element


class _WrappedImage:
    def rename(self, _name: str):
        return self


def _inputs() -> NotebookSupportInputs:
    array = np.ones((12, 12), dtype=np.float32)
    return NotebookSupportInputs(
        asc_vv=array,
        asc_vh=array,
        desc_vv=array,
        desc_vh=array,
        thermal_delta_raw=array,
        source_counts={"s1_ascending": 1, "s1_descending": 1, "landsat_day": 1, "modis_night": 1},
    )


def test_speckle_filter_rewraps_copy_properties_element_as_image(monkeypatch) -> None:
    image = _FakeEeImage()
    wrapped = _WrappedImage()
    coerced: list[object] = []

    def fake_ee_image(value):
        coerced.append(value)
        return wrapped

    monkeypatch.setattr(nb_exact_support.ee, "Image", fake_ee_image)

    result = _speckle_filter(image)

    assert result is wrapped
    assert result.rename("S1_ASC_VV_Filtered") is wrapped
    assert image.focal_mean_call == (1.5, "circle", "pixels")
    assert image.copy_properties_call == (image, ["system:time_start"])
    assert coerced == [image.element]


def test_default_support_input_path_uses_returned_inputs_without_calling_them(monkeypatch) -> None:
    expected = _inputs()
    settings = object()
    grid_spec = object()
    calls: list[tuple[object, object]] = []

    def fake_create(actual_settings, actual_grid_spec):
        calls.append((actual_settings, actual_grid_spec))
        return expected

    monkeypatch.setattr(nb_exact_support, "create_ee_notebook_support_fetcher", fake_create)

    actual = _resolve_support_inputs(
        settings=settings,
        grid_spec=grid_spec,
        support_fetcher=None,
    )

    assert actual is expected
    assert calls == [(settings, grid_spec)]


def test_injected_support_fetcher_remains_callable() -> None:
    expected = _inputs()
    grid_spec = object()
    calls: list[object] = []

    def fetcher(*, grid_spec):
        calls.append(grid_spec)
        return expected

    actual = _resolve_support_inputs(
        settings=object(),
        grid_spec=grid_spec,
        support_fetcher=fetcher,
    )

    assert actual is expected
    assert calls == [grid_spec]
