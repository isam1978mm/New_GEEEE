# INT-1 D1C StatueLogic source-intermediate export cell

This temporary Colab cell exports the raw mixed-resolution notebook intermediate for the final remaining INT-1 output:

- `AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif`

Why this exists:

- Notebook cell 101 computes `s2.select('B11').subtract(s2.select('B4'))` before final 10 m grid export.
- `B11` and `B4` have different native Sentinel-2 resolutions.
- Exporting/reprojecting each band to 10 m first and subtracting locally is not bitwise equivalent to Earth Engine's expression/reprojection order.
- This cell exports the raw `B11 - B4` intermediate on the D1C grid; the canonical app writer still applies the notebook `unitScale(0, 0.3)` formula.

Run it only after the D1C coordinate, D1C `GRID['crsTransform']`, DEM, and zero-shift gate have passed.

It writes/downloads:

- `S2_STATUELOGIC_RAW_DIFF_640.npy`

Do not commit this output.

```python
# EXPORT INT-1 cell-101 StatueLogic raw mixed-resolution source intermediate
import os, zipfile, shutil
import numpy as np
import ee
from google.colab import files

run = PATHS["run"]
drive_run = PATHS_DRIVE_GLOBAL["run"]

CRS = GRID["CRS"]
SCALE = float(GRID["SCALE"])
OUT_SIZE = int(GRID["OUT_SIZE"])
ct = [float(x) for x in GRID["crsTransform"]]
bounds = [float(x) for x in GRID["bounds_utm"]]
DEFAULT_FILL = -9999.0

roi = ee.Geometry.Rectangle(bounds, CRS, False)
s2_cell101 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(roi)
    .filterDate("2022-01-01", "2026-03-01")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 5))
    .median()
    .clip(roi)
)

statue_raw_diff = (
    s2_cell101.select("B11")
    .subtract(s2_cell101.select("B4"))
    .rename("S2_STATUELOGIC_RAW_DIFF_640")
    .toFloat()
    .reproject(crs=CRS, crsTransform=ee.List(ct))
)


def read_tile(image, x0, y0, x1, y1):
    tile_geo = ee.Geometry.Rectangle([x0, y0, x1, y1], CRS, False)
    rect = image.sampleRectangle(
        region=tile_geo,
        defaultValue=DEFAULT_FILL,
    ).getInfo()
    arr = np.array(rect["properties"]["S2_STATUELOGIC_RAW_DIFF_640"], dtype=np.float32)
    arr[arr == DEFAULT_FILL] = np.nan
    return arr

TILE = 320
arr = np.full((OUT_SIZE, OUT_SIZE), np.nan, dtype=np.float32)
xmin, ymin, xmax, ymax = bounds

for ty in range(OUT_SIZE // TILE):
    for tx in range(OUT_SIZE // TILE):
        x0 = xmin + tx * TILE * SCALE
        x1 = x0 + TILE * SCALE
        y1 = ymax - ty * TILE * SCALE
        y0 = y1 - TILE * SCALE

        tile = read_tile(statue_raw_diff, x0, y0, x1, y1)
        arr[ty*TILE:(ty+1)*TILE, tx*TILE:(tx+1)*TILE] = tile[:TILE, :TILE]
        print(f"✅ StatueLogic raw diff tile ({ty+1},{tx+1})")

name = "S2_STATUELOGIC_RAW_DIFF_640.npy"
np.save(os.path.join(run, name), arr)
shutil.copy2(os.path.join(run, name), os.path.join(drive_run, name))

print("statue raw diff shape:", arr.shape)
print("statue raw diff finite:", int(np.isfinite(arr).sum()), "nan:", int(np.isnan(arr).sum()))

zip_path = "/content/INT_1_D1C_GRID_STATUELOGIC_SOURCE_INPUTS.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(run, name), arcname=name)
    print("zipped:", name)

print("ZIP:", zip_path)
files.download(zip_path)
```
