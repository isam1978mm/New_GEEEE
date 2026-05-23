from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


POST_RTC_BANDS = {
    "VV_dB": "VV_dB.npy",
    "VH_dB": "VH_dB.npy",
    "logRatio_dB": "logRatio_dB.npy",
    "incidence": "incidence.npy",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export local-only app-side Cell 25 SAR intermediates into the F24 manifest layout."
    )
    parser.add_argument("--app-run-dir", type=Path, required=True, help="App run directory under data/runs/<run_id>.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for the local-only intermediate manifest. Defaults to qa/sar/intermediates under the run.",
    )
    return parser.parse_args()


def export_app_post_rtc_manifest(*, app_run_dir: Path, output_dir: Path | None = None) -> Path:
    base_output_dir = output_dir or (app_run_dir / "qa" / "sar" / "intermediates")
    post_rtc_dir = base_output_dir / "post_rtc"
    post_rtc_dir.mkdir(parents=True, exist_ok=True)

    bands: dict[str, str] = {}
    for band_name, filename in POST_RTC_BANDS.items():
        source_path = app_run_dir / "npy_radar_bands" / filename
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        destination = post_rtc_dir / filename
        shutil.copyfile(source_path, destination)
        bands[band_name] = f"post_rtc/{filename}"

    manifest = {
        "artifact_class": "FILESYSTEM_ONLY",
        "local_only": True,
        "source_profile": "cell25_pixel_export",
        "stages": {
            "post_rtc": {
                "label": "final",
                "bands": bands,
            }
        },
        "missing_stages": [
            "per_image_products_db",
            "pair_median",
            "final_median_pre_rtc",
            "post_sample_pre_rtc",
        ],
        "recommended_next_action": (
            "Add notebook-side and optional app-side pre-RTC intermediate captures in the same manifest layout "
            "to localize the first Cell 25 SAR divergence."
        ),
    }
    manifest_path = base_output_dir / "sar_intermediate_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def main() -> int:
    args = parse_args()
    manifest_path = export_app_post_rtc_manifest(app_run_dir=args.app_run_dir, output_dir=args.output_dir)
    print("Wrote local-only SAR intermediate manifest.")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
