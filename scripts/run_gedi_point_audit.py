"""Initialize Earth Engine, then run the read-only GEDI point-pair audit.

This bootstrap exists because ``audit_gedi_point_pairs.py`` constructs an Earth
Engine geometry during ``audit()``.  The Earth Engine client must be initialized
before that geometry is created.  Keeping the initialization here avoids any
import-time side effects in the testable point-pairing helpers.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import Settings  # noqa: E402
from app.services.ee_session import initialize_ee_session  # noqa: E402
from audit_gedi_point_pairs import main as audit_main  # noqa: E402


def main() -> int:
    initialize_ee_session(Settings())
    return audit_main()


if __name__ == "__main__":
    raise SystemExit(main())
