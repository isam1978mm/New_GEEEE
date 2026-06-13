# V6 Generator Tracking Checklist

## Status Correction

This checklist has been superseded by the corrected real-generation checklist:

```text
docs/V6_REAL_GENERATION_TRACKING_CHECKLIST.md
```

The earlier `V6-GENERATOR-2` and `V6-GENERATOR-3` work is scaffold/package-writer work only.

It proves:

- package role creation;
- inventory JSON creation;
- ZIP creation;
- validation report creation;
- safe CLI output;
- fixture-based tests.

It does not prove real V6 geospatial generation.

Current scaffold status:

```text
same output roles: yes
same real geospatial outputs: no
real coordinates: no
fake coordinates: no
empty safe GeoJSON shell: yes
Earth Engine: no
app button/download flow: no
```

## Current Next Step

```text
V6-REAL-GEE-1: implement the app-side Earth Engine runtime boundary and AOI/grid logic.
```

Do not continue expanding scaffold-only generation until the real generation path is started.
