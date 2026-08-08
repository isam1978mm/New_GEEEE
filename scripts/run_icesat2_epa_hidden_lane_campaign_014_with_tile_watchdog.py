"""Run Campaign 014 with a strict watchdog around each live ATL08 tile query.

This launcher changes only Campaign 014 execution. It installs the approved
EPA Hidden Lane recent-earthwork campaign, then replaces the live SlideRule
ATL08 query hook with a subprocess-backed wall-clock watchdog.

In addition to the wall-clock timeout, the parent captures worker stdout/stderr
and rejects a tile when SlideRule reports a resource/H5Coro read failure even if
other partial data were returned successfully. This prevents a partial ATL08
response from being cached and later mistaken for a scientifically complete
zero-result.

Scientific thresholds, source/event gates, finalizers, and application behavior
are unchanged.
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

import scan_icesat2_epa_hidden_lane_recent_earthwork_campaign as campaign014

DEFAULT_ATL08_TILE_TIMEOUT_SECONDS = 300.0
WORKER_FLAG = "--campaign014-atl08-worker"
_ORIGINAL_QUERY_ATL08 = campaign014.campaign._query_atl08
_PARTIAL_READ_MARKERS = (
    "H5Coro::Future read failure",
    "Failure on resource ",
)


class Campaign014TileTimeoutError(RuntimeError):
    """Raised when one Campaign 014 ATL08 tile exceeds its wall-clock limit."""


class Campaign014PartialReadError(RuntimeError):
    """Raised when SlideRule returns data while reporting a resource read failure."""


def _worker_main(
    request_path: Path,
    result_path: Path,
    error_path: Path,
) -> int:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    try:
        frame = _ORIGINAL_QUERY_ATL08(
            polygon=request["polygon"],
            start=str(request["start"]),
            end=str(request["end"]),
        )
        with result_path.open("wb") as stream:
            pickle.dump(frame, stream, protocol=pickle.HIGHEST_PROTOCOL)
    except BaseException as exc:  # noqa: BLE001 - child failure must reach parent
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


def _partial_read_lines(stdout: object, stderr: object) -> list[str]:
    """Return unique SlideRule resource/H5Coro failure lines from child output."""

    lines: list[str] = []
    seen: set[str] = set()
    for raw_text in (stdout, stderr):
        if not isinstance(raw_text, str):
            continue
        for raw_line in raw_text.splitlines():
            line = raw_line.strip()
            if not line or line in seen:
                continue
            if any(marker in line for marker in _PARTIAL_READ_MARKERS):
                lines.append(line)
                seen.add(line)
    return lines


def _query_atl08_with_timeout(
    *,
    polygon: list[dict[str, float]],
    start: str,
    end: str,
    timeout_seconds: float = DEFAULT_ATL08_TILE_TIMEOUT_SECONDS,
):
    if timeout_seconds <= 0:
        raise ValueError("ATL08 tile timeout must be positive")

    with tempfile.TemporaryDirectory(prefix="campaign014_atl08_") as temp_name:
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
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise Campaign014TileTimeoutError(
                "Campaign 014 ATL08 tile query exceeded "
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
                "Campaign 014 ATL08 worker exited without a result "
                f"(exit code {completed.returncode})"
            )

        partial_failures = _partial_read_lines(
            getattr(completed, "stdout", ""),
            getattr(completed, "stderr", ""),
        )
        if partial_failures:
            details = " | ".join(partial_failures[:8])
            raise Campaign014PartialReadError(
                "Campaign 014 ATL08 tile returned partial data with SlideRule "
                f"resource-read failures: {details}"
            )

        if not result_path.is_file():
            raise RuntimeError("Campaign 014 ATL08 worker produced no result file")

        with result_path.open("rb") as stream:
            return pickle.load(stream)


def install_timeout_hook() -> None:
    campaign014.install_campaign()
    campaign014.campaign._query_atl08 = _query_atl08_with_timeout


def main() -> int:
    install_timeout_hook()
    return campaign014.campaign.main()


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == WORKER_FLAG:
        if len(sys.argv) != 5:
            print("Campaign 014 ATL08 worker received invalid arguments", file=sys.stderr)
            raise SystemExit(2)
        raise SystemExit(
            _worker_main(
                Path(sys.argv[2]),
                Path(sys.argv[3]),
                Path(sys.argv[4]),
            )
        )
    raise SystemExit(main())
