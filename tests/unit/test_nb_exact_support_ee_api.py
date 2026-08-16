from __future__ import annotations

from app.pipeline.stages.nb_exact_support import _speckle_filter


class _FakeEeImage:
    def __init__(self) -> None:
        self.focal_mean_call: tuple[float, str, str] | None = None
        self.copy_properties_call: tuple[object, object] | None = None

    def focalMean(self, *, radius: float, kernelType: str, units: str):
        self.focal_mean_call = (radius, kernelType, units)
        return self

    def propertyNames(self):
        return ["system:time_start"]

    def copyProperties(self, source, properties):
        self.copy_properties_call = (source, properties)
        return self


def test_speckle_filter_uses_earth_engine_python_focal_mean_api() -> None:
    image = _FakeEeImage()

    result = _speckle_filter(image)

    assert result is image
    assert image.focal_mean_call == (1.5, "circle", "pixels")
    assert image.copy_properties_call == (image, ["system:time_start"])
