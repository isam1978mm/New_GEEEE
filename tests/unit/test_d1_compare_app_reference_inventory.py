from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import d1_compare_app_reference_inventory as compare


def test_family_from_path() -> None:
    assert compare._family_from_reference_path("bundle/artifacts/dem/file.tif") == "dem"
