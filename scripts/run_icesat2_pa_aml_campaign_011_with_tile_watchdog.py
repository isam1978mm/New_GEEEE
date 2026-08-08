"""Resume Campaign 011 with a hard watchdog around each live ATL08 tile query.

The original Campaign 011 scanner correctly caches each completed tile, but the
underlying SlideRule ATL08 call has no per-request wall-clock timeout. A remote
request can therefore stall the whole statewide scan indefinitely.

This launcher changes only Campaign 011 execution. It imports the approved
Campaign 011 scanner, replaces its live ATL08 query hook with a subprocess-backed
watchdog, and then invokes the normal scanner. Existing successful tile caches
remain valid and are reused. Scientific thresholds, polygon gates, finalizers,
and application behavior are unchanged.
"""

from __future__ import annotations

import json
import pickle
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import scan_icesat2_pa_aml_reclamation_complete_campaign as campaign011

DEFAULT_ATL08_TILE_TIMEOUT_SECONDS = 300.0
WORKER_FLAG = "--campaign011-atl08-worker"
_ORIGINAL_QUERY_ATL08 = campaign011.campaign._query_atl08


class Campaign011TileTimeoutError(RuntimeError):
    """Raised when one Campaign 011 ATL08 tile exceeds its wall-clock limit."""


def _worker_main(
    request_path: Path,
    result_path: Path,
    error_path: Path,
) -> int:
    """Run one original ATL08 query in an isolated child process."""

    request = json.loads(request_path.read_text(encoding="utf-8"))
    try:
        frame = _ORIGINAL_QUERY_ATL08(
            polygon=request["polygon"],
            start=str(request["start"]),
            end=str(request["end"]),
        )
        with result_path.open("wb") as stream:
            pickle.dump(frame, stream, protocol=pickle.HIGHEST_PROTOCOL)
    except BaseException as exc:  # noqa: BLE001 - serialize child failure to parent
        error_path.write_text(
            json.dumps(
                {
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return 1
    return 0


def _query_atl08_with_timeout(
    *,
    polygon: list[dict[str, float]],
    start: str,
    end: str,
    timeout_seconds: float = DEFAULT_ATL08_TILE_TIMEOUT_SECONDS,
):
    """Run one ATL08 query out-of-process and terminate it at the hard limit."""

    if timeout_seconds <= 0:
        raise ValueError("ATL08 tile timeout must be positive")

    with tempfile.TemporaryDirectory(prefix="campaign011_atl08_") as temp_name:
        temp_dir = Path(temp_name)
        request_path = temp_dir / "request.json"
        result_path = temp_dir / "result.pkl"
        error_path = temp_dir / "error.json"
        request_path.write_text(
            json.dumps(
                {
                    "polygon": polygon,
                    "start": start,
                    "end": end,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            WORKER_FLAG,
            str(request_path),
            str(result_path),
            str(error_path),
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise Campaign011TileTimeoutError(
                "Campaign 011 ATL08 tile query exceeded "
                f"{timeout_seconds:.0f} seconds"
            ) from exc

        if error_path.is_file():
            payload: Any = json.loads(error_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                error_type = payload.get("error_type") or "ATL08WorkerError"
                message = payload.get("error") or "unknown child-process failure"
            else:
                error_type = "ATL08WorkerError"
                message = "malformed child-process error payload"
            raise RuntimeError(f"{error_type}: {message}")

        if completed.returncode != 0:
            raise RuntimeError(
                "Campaign 011 ATL08 worker exited without a result "
                f"(exit code {completed.returncode})"
            )
        if not result_path.is_file():
            raise RuntimeError("Campaign 011 ATL08 worker produced no result file")

        with result_path.open("rb") as stream:
            return pickle.load(stream)


def install_timeout_hook() -> None:
    """Install only the live ATL08 query watchdog for Campaign 011."""

    campaign011.campaign._query_atl08 = _query_atl08_with_timeout


def main() -> int:
    install_timeout_hook()
    return campaign011.main()


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == WORKER_FLAG:
        if len(sys.argv) != 5:
            print("Campaign 011 ATL08 worker received invalid arguments", file=sys.stderr)
            raise SystemExit(2)
        raise SystemExit(
            _worker_main(
                Path(sys.argv[2]),
                Path(sys.argv[3]),
                Path(sys.argv[4]),
            )
        )
    raise SystemExit(main())
