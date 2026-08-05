from __future__ import annotations

import pytest

from scripts.probe_tyrone_3x_historical_naip import (
    TYRONE_3X_BBOX,
    TYRONE_3X_BBOX_TEXT,
    build_probe_argv,
)
from scripts.probe_tyrone_historical_naip import build_parser


def test_verified_3x_bbox_is_northern_r1_block() -> None:
    west, south, east, north = TYRONE_3X_BBOX
    assert west == pytest.approx(-108.42737364630895)
    assert south == pytest.approx(32.69235978274562)
    assert east == pytest.approx(-108.37347472926179)
    assert north == pytest.approx(32.71503710254814)
    assert south > 32.6923


def test_wrapper_injects_verified_bbox_as_single_safe_argument() -> None:
    argv = build_probe_argv(["--output-dir", "out", "--ee-project", "example"])
    assert argv[0] == f"--bbox={TYRONE_3X_BBOX_TEXT}"
    assert argv[1:] == ["--output-dir", "out", "--ee-project", "example"]


def test_injected_negative_bbox_parses_without_expected_argument_error() -> None:
    argv = build_probe_argv(["--output-dir", "out", "--ee-project", "example"])
    parsed = build_parser().parse_args(argv)
    assert parsed.bbox == TYRONE_3X_BBOX_TEXT
    assert str(parsed.output_dir) == "out"
    assert parsed.ee_project == "example"


@pytest.mark.parametrize("argument", ["--bbox", "--bbox=-108,32,-107,33"])
def test_wrapper_rejects_conflicting_bbox(argument: str) -> None:
    with pytest.raises(ValueError, match="fixes the R1C1/R1C2 AOI"):
        build_probe_argv([argument])
