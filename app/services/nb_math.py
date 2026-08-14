from __future__ import annotations

from typing import Any

import numpy as np


def clamp01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def norm01(array: np.ndarray) -> np.ndarray:
    """Notebook-style robust 2nd/98th percentile normalization to 0..1."""
    source = np.asarray(array, dtype=np.float32)
    valid = np.isfinite(source)
    if int(valid.sum()) < 10:
        return np.zeros(source.shape, dtype=np.float32)
    p2, p98 = np.nanpercentile(source[valid], [2.0, 98.0])
    if not np.isfinite(p2) or not np.isfinite(p98) or abs(float(p98 - p2)) < 1e-6:
        return np.zeros(source.shape, dtype=np.float32)
    out = np.zeros(source.shape, dtype=np.float32)
    out[valid] = np.clip((source[valid] - p2) / (p98 - p2), 0.0, 1.0).astype(np.float32)
    return out


def _median_filter(array: np.ndarray, *, size: int) -> np.ndarray:
    """Chunked NumPy median filter so NB results add no runtime dependency."""
    if size < 1 or size % 2 == 0:
        raise ValueError("Median-filter size must be a positive odd integer.")
    source = np.asarray(array, dtype=np.float32)
    finite = np.isfinite(source)
    fill = np.float32(np.nanmedian(source[finite])) if finite.any() else np.float32(0.0)
    filled = np.where(finite, source, fill).astype(np.float32)
    radius = size // 2
    padded = np.pad(filled, radius, mode="edge")
    output = np.empty(source.shape, dtype=np.float32)
    for row_start in range(0, source.shape[0], 32):
        row_end = min(source.shape[0], row_start + 32)
        block = padded[row_start : row_end + 2 * radius, :]
        windows = np.lib.stride_tricks.sliding_window_view(block, (size, size))
        output[row_start:row_end, :] = np.median(windows, axis=(-2, -1)).astype(np.float32)
    return output


def local_contrast(array: np.ndarray, *, size: int = 11) -> np.ndarray:
    return norm01(np.abs(np.asarray(array, dtype=np.float32) - _median_filter(array, size=size)))


def build_proxy_layers(
    *,
    vv: np.ndarray,
    vh: np.ndarray,
    ratio: np.ndarray,
    gold: np.ndarray,
    silver: np.ndarray,
    thermal_day: np.ndarray,
    thermal_inertia: np.ndarray,
    rough: np.ndarray,
    curv: np.ndarray,
    tpi: np.ndarray,
    vegroot: np.ndarray,
    clay_thermal: np.ndarray,
    thermal_delta: np.ndarray,
) -> dict[str, np.ndarray]:
    vv_n = norm01(vv)
    vh_n = norm01(vh)
    ratio_n = norm01(ratio)
    silver_n = norm01(silver)
    thermal_n = norm01(thermal_inertia)
    thermal_day_n = norm01(thermal_day)
    rough_n = norm01(rough)
    curv_n = norm01(curv)
    tpi_n = norm01(tpi)
    vegroot_n = norm01(vegroot)
    clay_n = norm01(clay_thermal)
    delta_n = norm01(thermal_delta)

    gold_contrast = local_contrast(gold)
    thermal_contrast = local_contrast(thermal_day)
    ratio_contrast = local_contrast(ratio_n)
    vv_contrast = local_contrast(vv_n, size=7)
    vh_contrast = local_contrast(vh_n, size=7)

    quartz = norm01(0.35 * gold_contrast + 0.25 * thermal_contrast + 0.20 * clay_n + 0.20 * rough_n)
    lime = norm01(
        0.30 * clay_n
        + 0.25 * rough_n
        + 0.20 * curv_n
        + 0.15 * tpi_n
        + 0.10 * thermal_contrast
        - 0.20 * vh_n
    )
    moist = norm01(0.35 * vegroot_n + 0.25 * (1.0 - thermal_day_n) + 0.20 * vh_n + 0.20 * ratio_contrast)
    oxid = norm01(0.50 * silver_n + 0.25 * clay_n + 0.25 * gold_contrast)
    sar_energy = norm01(0.45 * vv_n + 0.35 * vh_n + 0.20 * ratio_n)
    sar_comp = norm01(0.55 * sar_energy + 0.25 * vv_contrast + 0.20 * vh_contrast)
    thermal_risk = norm01(0.50 * thermal_contrast + 0.30 * delta_n + 0.20 * thermal_n)
    false_risk = norm01(0.28 * quartz + 0.22 * lime + 0.20 * moist + 0.18 * oxid + 0.12 * thermal_risk)
    return {
        "quartz": quartz,
        "lime": lime,
        "moist": moist,
        "oxid": oxid,
        "sar_comp": sar_comp,
        "risk": false_risk,
    }


def compute_point(values: dict[str, float | None]) -> dict[str, Any]:
    """Apply extracted new.ipynb formulas, abstaining when a required input is missing."""
    def has(*names: str) -> bool:
        for name in names:
            value = values.get(name)
            if value is None:
                return False
            try:
                if not np.isfinite(float(value)):
                    return False
            except (TypeError, ValueError):
                return False
        return True

    def v(name: str) -> float:
        return float(values[name])

    metal = (
        clamp01(0.40 * v("gold") + 0.25 * v("silver") + 0.25 * v("mass") + 0.10 * v("sar_comp"))
        if has("gold", "silver", "mass", "sar_comp")
        else None
    )
    void = (
        clamp01(0.45 * v("tunnel") + 0.25 * v("door") + 0.15 * v("tpi") + 0.15 * v("rough"))
        if has("tunnel", "door", "tpi", "rough")
        else None
    )
    ceramic = (
        clamp01(0.60 * v("pottery") + 0.20 * v("lime") + 0.20 * v("curv"))
        if has("pottery", "lime", "curv")
        else None
    )
    false_sig = (
        clamp01(
            0.35 * v("risk")
            + 0.20 * v("quartz")
            + 0.20 * v("lime")
            + 0.15 * v("moist")
            + 0.10 * v("oxid")
        )
        if has("risk", "quartz", "lime", "moist", "oxid")
        else None
    )

    best = None
    best_score = None
    if (
        metal is not None
        and void is not None
        and ceramic is not None
        and false_sig is not None
        and has("mass", "door", "rough", "tunnel", "sar_comp", "gold", "silver", "ascdesc", "moist")
    ):
        sarcophagus = clamp01(0.35 * void + 0.30 * v("mass") + 0.20 * v("door") + 0.15 * v("rough"))
        ran = clamp01(0.35 * v("mass") + 0.30 * v("door") + 0.20 * v("tunnel") + 0.15 * v("sar_comp"))
        statue = clamp01(0.35 * v("mass") + 0.25 * v("gold") + 0.20 * v("silver") + 0.20 * v("ascdesc"))
        scores = {
            "jar_جرة": ceramic * clamp01(0.7 + 0.3 * void) * (1.0 - 0.35 * false_sig),
            "chest_صندوق": metal * clamp01(0.6 + 0.4 * v("mass")) * (1.0 - 0.30 * false_sig),
            "sarcophagus_تابوت": sarcophagus * (1.0 - 0.25 * false_sig),
            "ran_ران": ran * (1.0 - 0.25 * false_sig),
            "statue_تمثال": statue * (1.0 - 0.30 * false_sig),
            "void_فراغ": void * (1.0 - 0.20 * v("moist")),
            "false_signature_وهم": false_sig,
        }
        best = max(scores, key=scores.get)
        best_score = round(float(scores[best]), 4)

    depth_m = None
    if void is not None and has("sar_comp", "thermal", "delta", "rough"):
        depth_m = round(
            float(
                np.clip(
                    0.6
                    + 1.2 * void
                    + 0.9 * v("sar_comp")
                    + 0.7 * v("thermal")
                    + 0.5 * v("delta")
                    + 0.4 * v("rough"),
                    0.4,
                    5.0,
                )
            ),
            2,
        )

    nano = round(v("nano_depth_penetration"), 6) if has("nano_depth_penetration") else None
    return {
        "nb_metal_signature": round(metal, 4) if metal is not None else None,
        "nb_void_signature": round(void, 4) if void is not None else None,
        "nb_ceramic_signature": round(ceramic, 4) if ceramic is not None else None,
        "nb_mass_signature": round(clamp01(v("mass")), 4) if has("mass") else None,
        "nb_false_signature_score": round(false_sig, 4) if false_sig is not None else None,
        "nb_best_object_interpretation": best,
        "nb_best_object_score": best_score,
        "nano_depth_penetration": nano,
        "nb_depth_m": depth_m,
        "nb_depth_available": depth_m is not None,
    }
