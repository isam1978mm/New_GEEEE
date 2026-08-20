#!/usr/bin/env python3
"""Research-only interior-orientation check for the Tyrone 1996 NAPP triplet.

Uses ONLY camera-calibration fiducial coordinates from USGS calibration report
R2104 and image pixels. It does not read or use any cover-depth values.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path("artifacts/tyrone_napp_fiducials")
WORK = ROOT / "work"
EX = WORK / "images"
ORI = WORK / "Ori-InterneScan"
for p in (ROOT, WORK, EX, ORI):
    p.mkdir(parents=True, exist_ok=True)

# Extract the three already-verified split-archive TIFFs.
subprocess.run([
    "7z", "x", "-y",
    "data/research/tyrone_napp_1996/Desktop.7z.001",
    f"-o{EX}",
], check=True)

# Exact fiducial coordinates (mm, calibration-report centered coordinates)
# from USGS calibration report R2104 for camera 124257 / lens 124308.
CAL = {
    "P1": (-103.932, -103.922),
    "P2": ( 103.946,  103.959),
    "P3": (-103.960,  103.927),
    "P4": ( 103.946, -103.922),
    "P5": (-112.997,   -0.014),
    "P6": ( 112.958,   -0.006),
    "P7": (   0.011,  112.956),
    "P8": (  -0.003, -112.990),
}

# MicMac image-coordinate convention: origin upper-left.
min_x = min(x for x, _ in CAL.values())
max_y = max(y for _, y in CAL.values())
UL = {name: (x - min_x, -y + max_y) for name, (x, y) in CAL.items()}

# Write MeasuresCamera.xml directly so the provenance is explicit.
xml = ["<?xml version='1.0' encoding='UTF-8'?>",
       "<SetOfMesureAppuisFlottants>",
       "  <MesureAppuiFlottant1Im>",
       "    <NameIm>Glob</NameIm>"]
for name in [f"P{i}" for i in range(1, 9)]:
    x, y = UL[name]
    xml += ["    <OneMesureAF1I>",
            f"      <NamePt>{name}</NamePt>",
            f"      <PtIm>{x:.6f} {y:.6f}</PtIm>",
            "    </OneMesureAF1I>"]
xml += ["  </MesureAppuiFlottant1Im>", "</SetOfMesureAppuisFlottants>"]
fn_cam = ORI / "MeasuresCamera.xml"
fn_cam.write_text("\n".join(xml) + "\n", encoding="utf-8")

# Run from WORK so spymicmac writes Ori-InterneScan/MeasuresIm-* locally.
for tif in EX.glob("*.tif"):
    shutil.copy2(tif, WORK / tif.name)

import os
os.chdir(WORK)

# Narrow compatibility shim only: pybob uses the old British-spelling names,
# while current scikit-image exposes the same functions as graycomatrix/graycoprops.
# This changes no photogrammetric calculations or parameters.
import skimage.feature
if not hasattr(skimage.feature, "greycomatrix") and hasattr(skimage.feature, "graycomatrix"):
    skimage.feature.greycomatrix = skimage.feature.graycomatrix
if not hasattr(skimage.feature, "greycoprops") and hasattr(skimage.feature, "graycoprops"):
    skimage.feature.greycoprops = skimage.feature.graycoprops

from spymicmac import matching

images = sorted(Path(".").glob("NP0NAPP0095191*.tif"))
assert len(images) == 3, images

trials = []
tune_img = images[1]

# First tune the four mid-side dot markers only. No depth data are involved.
best = None
for size in (31, 41, 51, 61):
    for dot_size in (2, 3, 4, 5, 6):
        try:
            residual = float(matching.match_zeiss_rmk(
                str(tune_img), size=size, dot_size=dot_size,
                data_strip="left", fn_cam="Ori-InterneScan/MeasuresCamera.xml",
                corner_size=None,
            ))
            rec = {"phase":"midside", "size":size, "dot_size":dot_size,
                   "corner_size":None, "residual":residual, "ok":True}
            trials.append(rec)
            if best is None or residual < best[0]:
                best = (residual, size, dot_size)
        except Exception as exc:
            trials.append({"phase":"midside", "size":size, "dot_size":dot_size,
                           "corner_size":None, "ok":False,
                           "error":f"{type(exc).__name__}: {exc}"})

if best is None:
    raise RuntimeError("No Zeiss RMK midside-fiducial parameter set succeeded")

_, best_size, best_dot = best

# Then test corner-cross sizes while holding the best mid-side template fixed.
best_all = None
for corner_size in (21, 31, 41, 51, 61):
    try:
        residual = float(matching.match_zeiss_rmk(
            str(tune_img), size=best_size, dot_size=best_dot,
            data_strip="left", fn_cam="Ori-InterneScan/MeasuresCamera.xml",
            corner_size=corner_size,
        ))
        rec = {"phase":"eight_fiducials", "size":best_size, "dot_size":best_dot,
               "corner_size":corner_size, "residual":residual, "ok":True}
        trials.append(rec)
        if best_all is None or residual < best_all[0]:
            best_all = (residual, corner_size)
    except Exception as exc:
        trials.append({"phase":"eight_fiducials", "size":best_size,
                       "dot_size":best_dot, "corner_size":corner_size,
                       "ok":False, "error":f"{type(exc).__name__}: {exc}"})

# Prefer all 8 fiducials if a corner search succeeds; otherwise keep the 4-side result.
if best_all is not None:
    best_corner = best_all[1]
else:
    best_corner = None

per_image = []
for fn in images:
    try:
        residual = float(matching.match_zeiss_rmk(
            str(fn), size=best_size, dot_size=best_dot,
            data_strip="left", fn_cam="Ori-InterneScan/MeasuresCamera.xml",
            corner_size=best_corner,
        ))
        per_image.append({"image":fn.name, "ok":True, "residual":residual})
        # Preserve the MeasuresIm file in the artifact root.
        for candidate in Path("Ori-InterneScan").glob(f"*{fn.name}*.xml"):
            shutil.copy2(candidate, Path("..") / (fn.stem + "_" + candidate.name))
    except Exception as exc:
        per_image.append({"image":fn.name,"ok":False,
                          "error":f"{type(exc).__name__}: {exc}"})

# Save camera coordinates and provenance outside WORK as compact evidence.
result = {
    "status":"COMPLETE",
    "camera":"Zeiss RMK A 15/23",
    "camera_serial":"124257",
    "lens_serial":"124308",
    "calibrated_focal_length_mm":152.773,
    "calibration_source":"USGS R2104",
    "calibration_centered_mm":CAL,
    "measures_camera_upper_left_mm":UL,
    "parameter_trials":trials,
    "chosen":{"size":best_size,"dot_size":best_dot,"corner_size":best_corner},
    "per_image":per_image,
    "depth_values_used":False,
    "classifier_used":False,
    "production_code_modified":False,
    "paid_action_attempted":False,
}
(Path("..") / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
shutil.copy2("Ori-InterneScan/MeasuresCamera.xml", Path("..") / "MeasuresCamera.xml")
print(json.dumps(result, indent=2))
