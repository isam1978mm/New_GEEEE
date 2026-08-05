from __future__ import annotations

import pytest

from scripts.probe_tyrone_3x_historical_naip import (
    TYRONE_3X_BBOX,
    TYRONE_3X_BBOX_TEXT,
    build_probe_argv,
)


def test_verified_3x_bbox_is_northern_r1_block() -> None:
    west, south, east, north = TYRONE_3X_BBOX
    assert west == pytest.approx(-108.42737364630895)
    assert south == pytest.approx(32.69235978274562)
    assert east == pytest.approx(-108.37347472926179)
    assert north == pytest.approx(32.71503710254814)
    assert south > 32.6923


def test_wrapper_injects_verified_bbox_before_other_arguments() -> None:
    argv = build_probe_argv(["--output-dir", "out", "--ee-project", "example"])
    assert argv[:2] == ["--bbox", TYRONE_3X_BBOX_TEXT]
    assert argv[2:] == ["--output-dir", "out", "--ee-project", "example"]


@pytest.mark.parametrize("argument", ["--bbox", "--bbox=-108,32,-107,33"])
def test_wrapper_rejects_conflicting_bbox(argument: str) -> None:
    with pytest.raises(ValueError, match="fixes the R1C1/R1C2 AOI"):
        build_probe_argv([argument])
