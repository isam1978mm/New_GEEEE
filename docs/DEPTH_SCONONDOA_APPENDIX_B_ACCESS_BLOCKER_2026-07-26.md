# Sconondoa Appendix B — Access Blocker — 2026-07-26

**Branch:** `main`  
**Current status:** blocked on file access  
**Usable calibration rows:** `0`  
**Numerical depth ready:** `no`

## What is confirmed

The official NYSDEC archive lists this file:

`Report.HW.727008.2021-06-25.FER Appendices A through C-Survey Figures and Photos.pdf`

Listed size: approximately 90 MB.

The required section is Appendix B, especially drawings B-1, B-2 and B-3. Those drawings are expected to contain the surveyed cell boundaries and as-built information needed to connect finite excavation-depth zones to Sentinel-1 pixels.

## Access attempts completed

- official NYSDEC file listing confirmed;
- direct browser fetch attempted;
- managed file download attempted;
- direct byte-range request attempted;
- exact-title and mirror searches attempted.

Results:

- the browser route returned a cache/fetch failure;
- the managed download failed;
- the local runtime could not resolve the NYSDEC host;
- no separate mirror or cached copy of the appendix was found.

## Decision

Do not invent cell geometry from the main report text or site address.

Do not run the Sentinel-1 depth-ordering screen until Appendix B is visibly reviewed.

```text
sconondoa_appendix_b_visible = no
surveyed_cell_geometry_extracted = no
earth_engine_query_executed = no
scientific_radar_linkage_outcome = not_evaluated
```

## Next step

Download the official 90 MB appendix locally and provide the PDF to the working session.

Then inspect drawings B-1, B-2 and B-3 and extract:

- exact cell boundaries;
- coordinate system and datum;
- final surface elevations;
- bottom-of-excavation elevations or finite depth annotations;
- cell names and comparable gravel-restored zones;
- stated survey accuracy or tolerance.

After that, create private shallow/deep GeoJSON polygons and run the committed Sconondoa depth-ordering screen.
