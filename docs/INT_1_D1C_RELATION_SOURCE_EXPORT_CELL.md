# INT-1 D1C relation source export cell

This temporary Colab cell exports the cell-90 Sentinel-2 source cube needed by the canonical INT-1 writer for the first three relation outputs:

- `AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif`
- `AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif`
- `AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif`

Run it only after the D1C coordinate, D1C `GRID['crsTransform']`, DEM, and zero-shift gate have passed.

It writes/downloads:

- `s2_relation_raw_cube.npy`
- `stage_s2_relation.manifest.json`

Do not commit these outputs.

```python
# EXPORT INT-1 cell-90 relation source cube for canonical app writer
import os, json, zipfile, shutil
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

source_bands = ["B2", "B3", "B4", "B8", "B11", "B12", "B1"]
DEFAULT_FILL = -9999.0

roi = ee.Geometry.Rectangle(bounds, CRS, False)
relation_img = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(roi)
    .filterDate("2024-01-01", "2026-03-01")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 5))
    .select(source_bands)
    .median()
    .toFloat()
    .reproject(crs=CRS, crsTransform=ee.List(ct))
)


def read_band_tile(image, band, x0, y0, x1, y1):
    tile_geo = ee.Geometry.Rectangle([x0, y0, x1, y1], CRS, False)
    rect = image.select(band).sampleRectangle(
        region=tile_geo,
        defaultValue=DEFAULT_FILL,
    ).getInfo()
    arr = np.array(rect["properties"][band], dtype=np.float32)
    arr[arr == DEFAULT_FILL] = np.nan
    return arr

TILE = 320
cube = np.full((OUT_SIZE, OUT_SIZE, len(source_bands)), np.nan, dtype=np.float32)
xmin, ymin, xmax, ymax = bounds

for ty in range(OUT_SIZE // TILE):
    for tx in range(OUT_SIZE // TILE):
        x0 = xmin + tx * TILE * SCALE
        x1 = x0 + TILE * SCALE
        y1 = ymax - ty * TILE * SCALE
        y0 = y1 - TILE * SCALE

        for bi, band in enumerate(source_bands):
            arr = read_band_tile(relation_img, band, x0, y0, x1, y1)
            cube[ty*TILE:(ty+1)*TILE, tx*TILE:(tx+1)*TILE, bi] = arr[:TILE, :TILE]

        print(f"✅ relation source tile ({ty+1},{tx+1})")

np.save(os.path.join(run, "s2_relation_raw_cube.npy"), cube)

manifest = {
    "stage_name": "stage_s2_relation",
    "status": "d1c_grid_relation_source_exported",
    "artifact_class": "LOCAL_SENSITIVE",
    "metadata": {
        "source_bands": source_bands,
        "layout": "HWC",
        "shape": list(cube.shape),
        "start_date": "2024-01-01",
        "end_date": "2026-03-01",
        "cloud_max": 5,
        "notebook_cell": 90,
    },
}

with open(os.path.join(run, "stage_s2_relation.manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

for name in ["s2_relation_raw_cube.npy", "stage_s2_relation.manifest.json"]:
    shutil.copy2(os.path.join(run, name), os.path.join(drive_run, name))
    print("copied to Drive:", name)

print("relation cube shape:", cube.shape)
print("relation cube finite:", int(np.isfinite(cube).sum()), "nan:", int(np.isnan(cube).sum()))

zip_path = "/content/INT_1_D1C_GRID_RELATION_SOURCE_INPUTS.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for name in ["s2_relation_raw_cube.npy", "stage_s2_relation.manifest.json"]:
        z.write(os.path.join(run, name), arcname=name)
        print("zipped:", name)

print("ZIP:", zip_path)
files.download(zip_path)
```
