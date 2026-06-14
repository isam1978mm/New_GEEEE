from __future__ import annotations

import argparse
from pathlib import Path

from app.config import Settings
from app.services.v6_local_package_input import ensure_local_v6_package_input


def main() -> int:
    parser = argparse.ArgumentParser(description="Create private local V6 package input for an existing run.")
    parser.add_argument("run_id", help="Existing local run id")
    parser.add_argument("--data-dir", default="data", help="Local data directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    settings = Settings(
        data_dir=data_dir,
        database_path=data_dir / "gee_screening.db",
        v6_package_flow_enabled=True,
        operator_auth_oidc_enabled=False,
        allow_network_bind=False,
    )
    result = ensure_local_v6_package_input(settings=settings, run_id=args.run_id)
    print(result.safe_summary)
    if result.created or result.reason == "already_exists":
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
