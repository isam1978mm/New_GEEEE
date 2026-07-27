"""Independently georeference the Plant Kraft AP-1 excavation-limit aerial.

The official Certification of CCR Removal contains Figure 3 as an embedded aerial
with a red excavation-limit overlay. This one-off utility extracts that image,
queries USGS/USDA NAIP imagery records, exports candidate orthoimages, estimates
feature-based homographies, and overlays the transformed red pixels for manual
review. It does not create an execution-ready polygon, call Earth Engine, or
create a calibration row.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import cv2
import fitz
import numpy as np
import requests
from PIL import Image

NAIP_SERVICE = (
    "https://imagery.nationalmap.gov/arcgis/rest/services/"
    "USGSNAIPImagery/ImageServer"
)
CENTER_LON = -81.1477777778
CENTER_LAT = 32.1483333333
BBOX_WGS84 = (-81.1545, 32.1448, -81.1411, 32.1524)
EXPORT_SIZE = (2400, 1361)
SOURCE_PAGE_1_BASED = 11


def request_json(url: str, params: dict[str, Any], timeout: int = 180) -> dict:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(f"ArcGIS error from {url}: {payload['error']}")
    return payload


def extract_source_aerial(pdf_path: Path, output_dir: Path) -> Path:
    document = fitz.open(pdf_path)
    try:
        page = document.load_page(SOURCE_PAGE_1_BASED - 1)
        images = page.get_images(full=True)
        if not images:
            raise RuntimeError("Figure 3 page contains no embedded image")
        # The first image is the full aerial with the excavation-limit overlay.
        xref = int(images[0][0])
        payload = document.extract_image(xref)
        extension = payload.get("ext", "png")
        destination = output_dir / f"figure3_excavation_limits_source.{extension}"
        destination.write_bytes(payload["image"])
        return destination
    finally:
        document.close()


def query_naip_records() -> dict:
    return request_json(
        f"{NAIP_SERVICE}/query",
        {
            "f": "json",
            "where": "1=1",
            "geometry": f"{CENTER_LON},{CENTER_LAT}",
            "geometryType": "esriGeometryPoint",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "false",
            "returnIdsOnly": "false",
            "resultRecordCount": 50,
        },
    )


def object_id_field(payload: dict) -> str:
    field = payload.get("objectIdFieldName")
    if isinstance(field, str) and field:
        return field
    for item in payload.get("fields", []):
        if item.get("type") == "esriFieldTypeOID":
            return str(item["name"])
    return "OBJECTID"


def extract_year(attributes: dict) -> int | None:
    for key, value in attributes.items():
        lowered = key.lower()
        if "year" in lowered:
            try:
                year = int(float(value))
                if 1990 <= year <= 2100:
                    return year
            except (TypeError, ValueError):
                continue
    for key, value in attributes.items():
        lowered = key.lower()
        if "date" not in lowered or value in (None, ""):
            continue
        try:
            number = int(value)
            if number > 10_000_000_000:
                number //= 1000
            from datetime import datetime, timezone

            return datetime.fromtimestamp(number, tz=timezone.utc).year
        except Exception:
            continue
    return None


def export_naip_image(record_id: int, destination: Path) -> None:
    mosaic_rule = {
        "mosaicMethod": "esriMosaicLockRaster",
        "lockRasterIds": [record_id],
        "ascending": True,
        "mosaicOperation": "MT_FIRST",
    }
    params = {
        "f": "image",
        "bbox": ",".join(str(value) for value in BBOX_WGS84),
        "bboxSR": 4326,
        "imageSR": 4326,
        "size": f"{EXPORT_SIZE[0]},{EXPORT_SIZE[1]}",
        "format": "jpgpng",
        "interpolation": "RSP_BilinearInterpolation",
        "renderingRule": json.dumps({"rasterFunction": "NaturalColor"}),
        "mosaicRule": json.dumps(mosaic_rule),
    }
    with requests.get(f"{NAIP_SERVICE}/exportImage", params=params, stream=True, timeout=(30, 600)) as response:
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    if destination.stat().st_size < 10_000:
        raise RuntimeError(f"NAIP export is unexpectedly small for record {record_id}")


def annotation_mask_rgb(image_rgb: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    saturated = hsv[:, :, 1] > 90
    red = ((hsv[:, :, 0] < 15) | (hsv[:, :, 0] > 168)) & saturated
    orange = (hsv[:, :, 0] >= 15) & (hsv[:, :, 0] <= 35) & saturated
    blue = (hsv[:, :, 0] >= 85) & (hsv[:, :, 0] <= 135) & saturated
    return (red | orange | blue).astype(np.uint8) * 255


def prepare_gray(image_rgb: np.ndarray, mask_annotations: bool) -> tuple[np.ndarray, np.ndarray | None]:
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    valid_mask: np.ndarray | None = None
    if mask_annotations:
        annotations = annotation_mask_rgb(image_rgb)
        annotations = cv2.dilate(annotations, np.ones((7, 7), np.uint8), iterations=2)
        valid_mask = cv2.bitwise_not(annotations)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    return gray, valid_mask


def estimate_homography(source_rgb: np.ndarray, target_rgb: np.ndarray) -> dict[str, Any]:
    source_gray, source_mask = prepare_gray(source_rgb, True)
    target_gray, target_mask = prepare_gray(target_rgb, False)

    detector = cv2.SIFT_create(nfeatures=8000, contrastThreshold=0.025, edgeThreshold=14)
    kp1, des1 = detector.detectAndCompute(source_gray, source_mask)
    kp2, des2 = detector.detectAndCompute(target_gray, target_mask)
    if des1 is None or des2 is None:
        raise RuntimeError("SIFT produced no descriptors")

    matcher = cv2.BFMatcher(cv2.NORM_L2)
    pairs = matcher.knnMatch(des1, des2, k=2)
    good = [first for first, second in pairs if first.distance < 0.72 * second.distance]
    if len(good) < 12:
        raise RuntimeError(f"Insufficient descriptor matches: {len(good)}")

    source_points = np.float32([kp1[item.queryIdx].pt for item in good]).reshape(-1, 1, 2)
    target_points = np.float32([kp2[item.trainIdx].pt for item in good]).reshape(-1, 1, 2)
    matrix, inlier_mask = cv2.findHomography(source_points, target_points, cv2.RANSAC, 5.0)
    if matrix is None or inlier_mask is None:
        raise RuntimeError("Homography estimation failed")

    inliers = inlier_mask.ravel().astype(bool)
    inlier_count = int(inliers.sum())
    projected = cv2.perspectiveTransform(source_points, matrix)
    errors = np.linalg.norm(projected[:, 0, :] - target_points[:, 0, :], axis=1)
    inlier_errors = errors[inliers]

    h, w = source_rgb.shape[:2]
    corners = np.float32([[[0, 0]], [[w - 1, 0]], [[w - 1, h - 1]], [[0, h - 1]]])
    transformed_corners = cv2.perspectiveTransform(corners, matrix)[:, 0, :]

    return {
        "matrix": matrix,
        "keypoints_source": kp1,
        "keypoints_target": kp2,
        "matches": good,
        "inlier_mask": inliers,
        "match_count": len(good),
        "inlier_count": inlier_count,
        "inlier_ratio": inlier_count / len(good),
        "median_inlier_error_px": float(np.median(inlier_errors)) if inlier_errors.size else math.inf,
        "max_inlier_error_px": float(np.max(inlier_errors)) if inlier_errors.size else math.inf,
        "transformed_source_corners_target_px": transformed_corners.tolist(),
    }


def save_match_visualization(source_rgb: np.ndarray, target_rgb: np.ndarray, result: dict[str, Any], destination: Path) -> None:
    match_mask = result["inlier_mask"].astype(np.uint8).tolist()
    visual = cv2.drawMatches(
        cv2.cvtColor(source_rgb, cv2.COLOR_RGB2BGR),
        result["keypoints_source"],
        cv2.cvtColor(target_rgb, cv2.COLOR_RGB2BGR),
        result["keypoints_target"],
        result["matches"],
        None,
        matchesMask=match_mask,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )
    cv2.imwrite(str(destination), visual)


def red_mask(image_rgb: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    mask1 = cv2.inRange(hsv, np.array([0, 100, 70]), np.array([13, 255, 255]))
    mask2 = cv2.inRange(hsv, np.array([170, 100, 70]), np.array([179, 255, 255]))
    mask = cv2.bitwise_or(mask1, mask2)
    # Exclude the figure-title region; the excavation boundary occupies the upper site area.
    mask[int(mask.shape[0] * 0.70) :, :] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if count <= 1:
        return mask
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return np.where(labels == largest, 255, 0).astype(np.uint8)


def target_pixels_to_wgs84(points: np.ndarray) -> np.ndarray:
    xmin, ymin, xmax, ymax = BBOX_WGS84
    width, height = EXPORT_SIZE
    longitude = xmin + points[:, 0] / (width - 1) * (xmax - xmin)
    latitude = ymax - points[:, 1] / (height - 1) * (ymax - ymin)
    return np.column_stack([longitude, latitude])


def save_red_overlay(source_rgb: np.ndarray, target_rgb: np.ndarray, matrix: np.ndarray, destination: Path) -> dict[str, Any]:
    mask = red_mask(source_rgb)
    y, x = np.where(mask > 0)
    source_points = np.column_stack([x, y]).astype(np.float32).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(source_points, matrix)[:, 0, :]

    overlay = cv2.cvtColor(target_rgb, cv2.COLOR_RGB2BGR)
    valid = (
        (transformed[:, 0] >= 0)
        & (transformed[:, 0] < overlay.shape[1])
        & (transformed[:, 1] >= 0)
        & (transformed[:, 1] < overlay.shape[0])
    )
    transformed_valid = transformed[valid]
    for px, py in np.rint(transformed_valid).astype(int):
        cv2.circle(overlay, (px, py), 2, (0, 0, 255), -1)
    cv2.imwrite(str(destination), overlay)

    if transformed_valid.size:
        bounds = [
            float(transformed_valid[:, 0].min()),
            float(transformed_valid[:, 1].min()),
            float(transformed_valid[:, 0].max()),
            float(transformed_valid[:, 1].max()),
        ]
        wgs84 = target_pixels_to_wgs84(transformed_valid)
        wgs84_bounds = [
            float(wgs84[:, 0].min()),
            float(wgs84[:, 1].min()),
            float(wgs84[:, 0].max()),
            float(wgs84[:, 1].max()),
        ]
    else:
        bounds = []
        wgs84_bounds = []
    return {
        "source_red_pixel_count": int(len(source_points)),
        "transformed_valid_red_pixel_count": int(len(transformed_valid)),
        "target_pixel_bounds": bounds,
        "wgs84_bounds": wgs84_bounds,
    }


def main() -> int:
    source_value = os.environ.get("PLANT_KRAFT_SOURCE_PDF")
    if not source_value:
        raise RuntimeError("PLANT_KRAFT_SOURCE_PDF is required")
    source_pdf = Path(source_value)

    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "artifacts" / "plant_kraft_ap1_georeference"
    naip_dir = output_dir / "naip_candidates"
    output_dir.mkdir(parents=True, exist_ok=True)
    naip_dir.mkdir(parents=True, exist_ok=True)

    source_path = extract_source_aerial(source_pdf, output_dir)
    source_rgb = np.array(Image.open(source_path).convert("RGB"))

    records_payload = query_naip_records()
    (output_dir / "naip_query.json").write_text(
        json.dumps(records_payload, indent=2), encoding="utf-8"
    )
    oid_field = object_id_field(records_payload)
    records: list[dict[str, Any]] = []
    for feature in records_payload.get("features", []):
        attributes = feature.get("attributes", {})
        try:
            oid = int(attributes[oid_field])
        except Exception:
            continue
        records.append({"object_id": oid, "year": extract_year(attributes), "attributes": attributes})
    records.sort(key=lambda item: (abs((item["year"] or 9999) - 2017), -(item["year"] or 0)))

    candidates: list[dict[str, Any]] = []
    for record in records[:16]:
        oid = record["object_id"]
        year = record["year"]
        image_path = naip_dir / f"naip_oid_{oid}_year_{year or 'unknown'}.png"
        candidate_report: dict[str, Any] = {
            "object_id": oid,
            "year": year,
            "attributes": record["attributes"],
            "image_file": str(image_path.relative_to(output_dir)),
        }
        try:
            export_naip_image(oid, image_path)
            target_rgb = np.array(Image.open(image_path).convert("RGB"))
            result = estimate_homography(source_rgb, target_rgb)
            candidate_report.update(
                {
                    "status": "MATCHED",
                    "match_count": result["match_count"],
                    "inlier_count": result["inlier_count"],
                    "inlier_ratio": result["inlier_ratio"],
                    "median_inlier_error_px": result["median_inlier_error_px"],
                    "max_inlier_error_px": result["max_inlier_error_px"],
                    "homography_source_to_target": result["matrix"].tolist(),
                    "transformed_source_corners_target_px": result[
                        "transformed_source_corners_target_px"
                    ],
                }
            )
            match_path = naip_dir / f"match_oid_{oid}.jpg"
            save_match_visualization(source_rgb, target_rgb, result, match_path)
            candidate_report["match_visualization"] = str(match_path.relative_to(output_dir))
        except Exception as exc:
            candidate_report.update({"status": "FAILED", "error": str(exc)})
        candidates.append(candidate_report)

    matched = [item for item in candidates if item.get("status") == "MATCHED"]
    matched.sort(
        key=lambda item: (
            -int(item["inlier_count"]),
            float(item["median_inlier_error_px"]),
        )
    )

    best_summary: dict[str, Any] | None = None
    if matched:
        best = matched[0]
        best_image = output_dir / str(best["image_file"])
        target_rgb = np.array(Image.open(best_image).convert("RGB"))
        matrix = np.array(best["homography_source_to_target"], dtype=np.float64)
        overlay_path = output_dir / "best_transformed_excavation_red_pixels.png"
        red_summary = save_red_overlay(source_rgb, target_rgb, matrix, overlay_path)
        best_summary = {
            "object_id": best["object_id"],
            "year": best["year"],
            "image_file": best["image_file"],
            "match_visualization": best.get("match_visualization"),
            "match_count": best["match_count"],
            "inlier_count": best["inlier_count"],
            "inlier_ratio": best["inlier_ratio"],
            "median_inlier_error_px": best["median_inlier_error_px"],
            "homography_source_to_target": best["homography_source_to_target"],
            "red_overlay_file": overlay_path.name,
            "red_overlay_summary": red_summary,
        }

    report = {
        "status": (
            "NAIP_GEOREFERENCE_CANDIDATE_CREATED_MANUAL_REVIEW_REQUIRED"
            if best_summary
            else "NAIP_GEOREFERENCE_FAILED"
        ),
        "source": "Georgia Power Certification of CCR Removal Figure 3",
        "control_source": "USGS/USDA NAIP imagery service",
        "source_aerial_file": source_path.name,
        "source_aerial_shape": list(source_rgb.shape),
        "naip_query_record_count": len(records),
        "bbox_wgs84": BBOX_WGS84,
        "export_size": EXPORT_SIZE,
        "candidates": candidates,
        "best_candidate": best_summary,
        "earth_engine_query_executed": False,
        "calibration_record_created": False,
        "execution_geojson_created": False,
        "decision": "HOLD_UNTIL_CONTROL_MATCHES_AND_EXCAVATION_BOUNDARY_ARE_MANUALLY_REVIEWED",
    }
    (output_dir / "georeference_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        "# Plant Kraft AP-1 independent georeference\n\n"
        "Review the best match visualization and transformed red-pixel overlay. "
        "The source is Georgia Power Figure 3; the independent control is USGS/USDA "
        "NAIP. This output is QA only. It does not create an execution GeoJSON, call "
        "Earth Engine, or create a calibration row.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0 if best_summary else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "GEOREFERENCE_FAILED", "error": str(exc)}), file=sys.stderr)
        raise
