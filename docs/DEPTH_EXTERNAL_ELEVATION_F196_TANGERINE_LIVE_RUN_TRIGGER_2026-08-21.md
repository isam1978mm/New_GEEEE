# F196 — Tangerine live execution trigger

Date: 2026-08-21

Purpose: run the already-merged F195 Tangerine analysis against the actual public 2015 and 2021 lidar from a GitHub Actions runner with outbound network access and PDAL available.

This branch does not modify the app, classifier, NB formula, production pipeline, or scientific gates.

The workflow executes only:

- `USGS_LPC_AZ_Eastern_PimaCO_2015_LAS_2017`
- `AZ_PimaCo_2_2021`
- the merged `scripts/tangerine_lidar_execution.py`
- default 1 m DTM resolution and default 1200 m analysis buffer
- the frozen F195 stable-ground residual gates

The OSM landfill polygon remains provisional execution geometry. It is sufficient for the first residual-gate execution but cannot support a final claim until checked against official survey `RS-33-039`.

No new site search is authorized.
