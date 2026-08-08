"""Run Campaign 014 with SlideRule plus direct NASA/NSIDC fallback.

Normal execution remains unchanged through the existing strict Campaign 014
watchdog: three broad SlideRule attempts, followed by explicit one-resource-at-a-
time SlideRule recovery.  If either of the two repeatedly unreadable ATL08 v007
resources still fails, this launcher substitutes only that resource with the
locally cached official NASA/NSIDC HDF5 copy created by
``recover_campaign_014_nsidc_atl08.py``.

Every CMR-listed resource must still be represented.  No resource may be
silently skipped.  Scientific thresholds, EPA gates, finalizers, and generic
application code remain unchanged.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import recover_campaign_014_nsidc_atl08 as direct
import run_icesat2_epa_hidden_lane_campaign_014_with_tile_watchdog as base


class Campaign014NsidcFallbackError(RuntimeError):
    """Raised when neither SlideRule nor direct NSIDC can complete a resource."""


def _recover_by_explicit_resources_with_nsidc(
    *,
    polygon: list[dict[str, float]],
    start: str,
    end: str,
    timeout_seconds: float,
    attempts: int = base.DEFAULT_ATL08_RESOURCE_ATTEMPTS,
):
    resources_value, cmr_failures = base._run_worker_request(
        {
            "operation": "cmr",
            "polygon": polygon,
            "start": start,
            "end": end,
        },
        timeout_seconds=timeout_seconds,
    )
    if cmr_failures:
        raise Campaign014NsidcFallbackError(
            "Campaign 014 CMR lookup reported resource-read failures: "
            + " | ".join(cmr_failures[:8])
        )
    resources = base._unique_resource_names(resources_value)
    print(
        "      broad ATL08 reads remained partial; "
        f"recovering {len(resources)} CMR-listed resources individually"
    )

    frames: list[Any] = []
    unresolved: list[dict[str, Any]] = []
    direct_used: list[str] = []

    for resource_index, resource in enumerate(resources, start=1):
        history: list[str] = []
        frame = None

        for attempt_number in range(1, attempts + 1):
            try:
                candidate, failures = base._run_worker_request(
                    {
                        "operation": "resource",
                        "resource": resource,
                        "polygon": polygon,
                        "start": start,
                        "end": end,
                    },
                    timeout_seconds=timeout_seconds,
                )
            except (base.Campaign014TileTimeoutError, RuntimeError) as exc:
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
            frame = candidate
            break

        if frame is None and resource in direct.UNRESOLVED_RESOURCES:
            try:
                frame = direct.load_cached_resource(resource, polygon=polygon)
                direct_used.append(resource)
                print(f"      NSIDC direct fallback recovered {resource}")
            except direct.Campaign014DirectRecoveryError as exc:
                history.append(f"NSIDC direct fallback: {exc}")

        if frame is None:
            unresolved.append(
                {
                    "resource": resource,
                    "sliderule_attempts": attempts,
                    "history": history[-14:],
                }
            )
        else:
            frames.append(frame)
            if resource_index == len(resources) or resource_index % 10 == 0:
                print(
                    "      explicit/direct recovery "
                    f"{resource_index}/{len(resources)}"
                )

    if unresolved:
        raise Campaign014NsidcFallbackError(
            "Campaign 014 remains incomplete after SlideRule and direct NSIDC "
            f"fallback; unresolved {len(unresolved)}/{len(resources)} resources: "
            + json.dumps(unresolved[:8], sort_keys=True)
        )

    combined = base._combine_resource_frames(frames)
    if hasattr(combined, "attrs"):
        combined.attrs["campaign014_nsidc_direct_resources"] = sorted(set(direct_used))
        combined.attrs["campaign014_all_cmr_resources_represented"] = True
    return combined


def _query_atl08_with_nsidc_fallback(
    *,
    polygon: list[dict[str, float]],
    start: str,
    end: str,
    timeout_seconds: float = base.DEFAULT_ATL08_TILE_TIMEOUT_SECONDS,
    attempts: int = base.DEFAULT_ATL08_TILE_ATTEMPTS,
):
    if timeout_seconds <= 0:
        raise ValueError("ATL08 tile timeout must be positive")
    if attempts <= 0:
        raise ValueError("ATL08 tile attempts must be positive")

    partial_history: list[list[str]] = []
    for _attempt_number in range(1, attempts + 1):
        frame, failures = base._run_worker_request(
            {
                "operation": "broad",
                "polygon": polygon,
                "start": start,
                "end": end,
            },
            timeout_seconds=timeout_seconds,
        )
        if failures:
            partial_history.append(failures)
            continue
        return frame

    try:
        return _recover_by_explicit_resources_with_nsidc(
            polygon=polygon,
            start=start,
            end=end,
            timeout_seconds=timeout_seconds,
        )
    except (Campaign014NsidcFallbackError, base.Campaign014ResourceRecoveryError) as exc:
        unique: list[str] = []
        seen: set[str] = set()
        for failures in partial_history:
            for line in failures:
                if line not in seen:
                    unique.append(line)
                    seen.add(line)
        raise Campaign014NsidcFallbackError(
            "Campaign 014 remained incomplete after broad SlideRule retries and "
            "explicit/direct recovery. Broad failures: "
            + " | ".join(unique[:12])
            + f". Recovery: {exc}"
        ) from exc


def install_recovery_hook() -> None:
    base.campaign014.install_campaign()
    base.campaign014.campaign._query_atl08 = _query_atl08_with_nsidc_fallback


def main() -> int:
    install_recovery_hook()
    return base.campaign014.campaign.main()


if __name__ == "__main__":
    raise SystemExit(main())
