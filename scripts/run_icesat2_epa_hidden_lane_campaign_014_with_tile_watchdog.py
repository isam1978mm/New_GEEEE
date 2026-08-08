"""Run Campaign 014 with strict broad-query and explicit-resource recovery.

This launcher changes only Campaign 014 execution. It installs the approved
EPA Hidden Lane recent-earthwork campaign, then replaces the live SlideRule
ATL08 query hook with a subprocess-backed wall-clock watchdog.

A tile first receives up to three normal full-query attempts. If every full
query reports a SlideRule resource/H5Coro read failure, the launcher uses the
SlideRule CMR client to enumerate every ATL08 release-007 granule intersecting
that tile and time range, then processes those resources one at a time. Each
resource also receives up to three attempts and is accepted only when no
resource/H5Coro failure is reported. The tile is returned only if every listed
resource is recovered cleanly.

Scientific thresholds, EPA source/event gates, finalizers, and application
behavior are unchanged.
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
DEFAULT_ATL08_TILE_ATTEMPTS = 3
DEFAULT_ATL08_RESOURCE_ATTEMPTS = 3
ATL08_CMR_SHORT_NAME = "ATL08"
ATL08_CMR_VERSION = "007"
WORKER_FLAG = "--campaign014-atl08-worker"
_ORIGINAL_QUERY_ATL08 = campaign014.campaign._query_atl08
_PARTIAL_READ_MARKERS = (
    "H5Coro::Future read failure",
    "Failure on resource ",
)


class Campaign014TileTimeoutError(RuntimeError):
    """Raised when one Campaign 014 ATL08 worker exceeds its wall-clock limit."""


class Campaign014PartialReadError(RuntimeError):
    """Raised when normal full-tile retries remain partial."""


class Campaign014ResourceRecoveryError(RuntimeError):
    """Raised when explicit per-resource recovery cannot make a complete tile."""


def _worker_main(
    request_path: Path,
    result_path: Path,
    error_path: Path,
) -> int:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    operation = str(request.get("operation") or "broad")
    polygon = request["polygon"]
    start = str(request["start"])
    end = str(request["end"])

    try:
        if operation == "broad":
            result = _ORIGINAL_QUERY_ATL08(
                polygon=polygon,
                start=start,
                end=end,
            )
        elif operation == "cmr":
            from sliderule import earthdata, icesat2

            icesat2.init(url="slideruleearth.io", rethrow=True)
            result = earthdata.cmr(
                short_name=ATL08_CMR_SHORT_NAME,
                version=ATL08_CMR_VERSION,
                polygon=polygon,
                time_start=start,
                time_end=end,
            )
        elif operation == "resource":
            resource = request.get("resource")
            if not isinstance(resource, str) or not resource.strip():
                raise ValueError("Campaign 014 resource worker requires a resource name")

            from sliderule import icesat2, sliderule

            icesat2.init(url="slideruleearth.io", rethrow=True)
            result = sliderule.run(
                "atl08x",
                {
                    "poly": polygon,
                    "t0": start,
                    "t1": end,
                },
                resources=[resource],
            )
        else:
            raise ValueError(f"unsupported Campaign 014 worker operation: {operation}")

        with result_path.open("wb") as stream:
            pickle.dump(result, stream, protocol=pickle.HIGHEST_PROTOCOL)
    except BaseException as exc:  # noqa: BLE001 - child failure must reach parent
        error_path.write_text(
            json.dumps(
                {
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "operation": operation,
                    "resource": request.get("resource"),
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


def _run_worker_request(
    request: dict[str, Any],
    *,
    timeout_seconds: float,
) -> tuple[Any, list[str]]:
    """Run one isolated worker request and return its result plus read alerts."""

    with tempfile.TemporaryDirectory(prefix="campaign014_atl08_") as temp_name:
        temp_dir = Path(temp_name)
        request_path = temp_dir / "request.json"
        result_path = temp_dir / "result.pkl"
        error_path = temp_dir / "error.json"
        request_path.write_text(
            json.dumps(request, sort_keys=True) + "\n",
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
            operation = request.get("operation") or "broad"
            resource = request.get("resource")
            suffix = f" for resource {resource}" if resource else ""
            raise Campaign014TileTimeoutError(
                "Campaign 014 ATL08 "
                f"{operation} worker exceeded {timeout_seconds:.0f} seconds{suffix}"
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
        if not result_path.is_file():
            raise RuntimeError("Campaign 014 ATL08 worker produced no result file")

        failures = _partial_read_lines(
            getattr(completed, "stdout", ""),
            getattr(completed, "stderr", ""),
        )
        with result_path.open("rb") as stream:
            result = pickle.load(stream)
        return result, failures


def _unique_resource_names(value: object) -> list[str]:
    if not isinstance(value, list):
        raise Campaign014ResourceRecoveryError(
            "Campaign 014 CMR resource lookup returned an unexpected result"
        )
    resources: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        resource = item.strip()
        if not resource or resource in seen:
            continue
        resources.append(resource)
        seen.add(resource)
    if not resources:
        raise Campaign014ResourceRecoveryError(
            "Campaign 014 CMR resource lookup returned no ATL08 release-007 granules"
        )
    return resources


def _combine_resource_frames(frames: list[Any]):
    if not frames:
        raise Campaign014ResourceRecoveryError(
            "Campaign 014 explicit-resource recovery produced no frames"
        )
    if len(frames) == 1:
        return frames[0]

    import pandas as pd

    combined = pd.concat(frames, axis=0)
    first_attrs = getattr(frames[0], "attrs", None)
    if isinstance(first_attrs, dict) and hasattr(combined, "attrs"):
        combined.attrs.update(first_attrs)
    return combined


def _recover_by_explicit_resources(
    *,
    polygon: list[dict[str, float]],
    start: str,
    end: str,
    timeout_seconds: float,
    attempts: int = DEFAULT_ATL08_RESOURCE_ATTEMPTS,
):
    """Enumerate CMR resources and require a clean result from every granule."""

    if attempts <= 0:
        raise ValueError("ATL08 resource attempts must be positive")

    resources_value, cmr_failures = _run_worker_request(
        {
            "operation": "cmr",
            "polygon": polygon,
            "start": start,
            "end": end,
        },
        timeout_seconds=timeout_seconds,
    )
    if cmr_failures:
        raise Campaign014ResourceRecoveryError(
            "Campaign 014 CMR lookup unexpectedly reported resource-read failures: "
            + " | ".join(cmr_failures[:8])
        )

    resources = _unique_resource_names(resources_value)
    print(
        "      broad ATL08 reads remained partial; "
        f"recovering {len(resources)} CMR-listed resources individually"
    )

    frames: list[Any] = []
    failed_resources: list[dict[str, Any]] = []

    for resource_index, resource in enumerate(resources, start=1):
        history: list[str] = []
        recovered = False
        for attempt_number in range(1, attempts + 1):
            try:
                frame, failures = _run_worker_request(
                    {
                        "operation": "resource",
                        "resource": resource,
                        "polygon": polygon,
                        "start": start,
                        "end": end,
                    },
                    timeout_seconds=timeout_seconds,
                )
            except (Campaign014TileTimeoutError, RuntimeError) as exc:
                history.append(
                    f"attempt {attempt_number}/{attempts}: {type(exc).__name__}: {exc}"
                )
                continue

            if failures:
                history.extend(
                    f"attempt {attempt_number}/{attempts}: {line}"
                    for line in failures[:8]
                )
                continue

            frames.append(frame)
            recovered = True
            break

        if not recovered:
            failed_resources.append(
                {
                    "resource": resource,
                    "attempts": attempts,
                    "history": history[-12:],
                }
            )
        elif resource_index == len(resources) or resource_index % 10 == 0:
            print(
                "      explicit-resource recovery "
                f"{resource_index}/{len(resources)}"
            )

    if failed_resources:
        details = json.dumps(failed_resources[:8], sort_keys=True)
        raise Campaign014ResourceRecoveryError(
            "Campaign 014 explicit-resource recovery remained incomplete; "
            f"failed {len(failed_resources)}/{len(resources)} CMR-listed resources: "
            + details
        )

    return _combine_resource_frames(frames)


def _query_atl08_with_timeout(
    *,
    polygon: list[dict[str, float]],
    start: str,
    end: str,
    timeout_seconds: float = DEFAULT_ATL08_TILE_TIMEOUT_SECONDS,
    attempts: int = DEFAULT_ATL08_TILE_ATTEMPTS,
):
    if timeout_seconds <= 0:
        raise ValueError("ATL08 tile timeout must be positive")
    if attempts <= 0:
        raise ValueError("ATL08 tile attempts must be positive")

    partial_history: list[list[str]] = []

    for attempt_number in range(1, attempts + 1):
        frame, partial_failures = _run_worker_request(
            {
                "operation": "broad",
                "polygon": polygon,
                "start": start,
                "end": end,
            },
            timeout_seconds=timeout_seconds,
        )
        if partial_failures:
            partial_history.append(partial_failures)
            continue
        return frame

    unique_failures: list[str] = []
    seen: set[str] = set()
    for failures in partial_history:
        for line in failures:
            if line not in seen:
                unique_failures.append(line)
                seen.add(line)

    try:
        return _recover_by_explicit_resources(
            polygon=polygon,
            start=start,
            end=end,
            timeout_seconds=timeout_seconds,
        )
    except Campaign014ResourceRecoveryError as exc:
        broad_details = " | ".join(unique_failures[:12])
        raise Campaign014ResourceRecoveryError(
            "Campaign 014 remained incomplete after broad-query retries and "
            f"explicit-resource recovery. Broad failures: {broad_details}. "
            f"Resource recovery: {exc}"
        ) from exc


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
