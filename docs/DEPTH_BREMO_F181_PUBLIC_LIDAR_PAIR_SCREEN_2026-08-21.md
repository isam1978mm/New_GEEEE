# F181 — Bremo public lidar-pair timing/coverage screen

Date: 2026-08-21

## Purpose

After freezing the independent `CBR-02` measured-thickness truth set in F180, identify a public lidar surface pair that independently brackets the 2019-2020 Visual Clean -> six-inch over-excavation interval at Bremo West Ash Pond.

Candidate selection was based only on timing, coverage, provenance, and published accuracy. The frozen Bremo thickness answers were not used to choose a dataset.

## Required time bracket

The CQA record establishes:

- CBR work resumed approximately 2019-09-28.
- Visual Clean areas were surveyed during the resumed work.
- six-inch over-excavation followed the Visual Clean survey.
- substantial completion was 2020-01-30.

A useful independent lidar pair would therefore need one surface representing the pre-over-excavation/VC condition and another representing the post-over-excavation condition, with spatial coverage over West Ash Pond.

## Candidate 1 — 2016 USGS Chesapeake Bay Virginia lidar

Official NOAA/USGS metadata identifies the `2016 USGS Lidar: Chesapeake Bay, VA` project.

Relevant facts:

- geographic coverage includes Fluvanna County;
- geographic extent includes Bremo;
- acquisition time frame: 2015-11-15 through 2016-03-30;
- nominal pulse spacing about 0.66-0.70 m;
- State Plane South / NAD83(2011), NAVD88 deliverables exist;
- tested non-vegetated vertical accuracy: RMSEz = 0.28 ft = 0.0853 m;
- dataset meets a 0.33 ft / 10 cm RMSEz vertical accuracy class.

### Decision

**FAIL for F180 truth-pair validation because of timing.**

The acquisition predates the 2019-2020 VC/six-inch interval by several years and also predates much of the documented 2016-2017 CCR excavation. It is not a representation of the VC baseline surface and cannot be paired directly with the 2020 over-excavated survey to recover the six-inch change.

It remains a valid historical Bremo elevation dataset for other questions, but not this measured-thickness interval.

## Candidate 2 — 2020 USGS Northern Shenandoah lidar

Official metadata for `2020 USGS Lidar: Northern Shenandoah, VA` gives:

- acquisition time frame approximately 2020-11-23 through 2020-12-30;
- southern geographic bound approximately 37.797597 N.

Bremo Power Station is approximately 37.7053 N.

### Decision

**FAIL — no Bremo coverage.**

The project stops roughly 0.09 degrees of latitude north of Bremo, so it cannot provide the post-excavation surface.

## 2019 Virginia 3DEP award screen

The FY18/19 USGS 3DEP award list identifies Virginia lidar projects for:

- City of Williamsburg; and
- Henrico County.

No Fluvanna/Bremo 2019 project is identified in that award list.

This does not prove no private/local 2019 survey exists, but it removes the obvious 2019 public 3DEP reflight route.

## F181 decision

### Public lidar before/after pair: FAIL

Current public lidar evidence does **not** provide two Bremo surfaces bracketing the 2019-2020 VC-to-over-excavation interval.

Known public lidar situation:

- usable Bremo-covering lidar exists from 2015-2016, with published RMSEz approximately 0.085 m in non-vegetated terrain;
- that surface is temporally wrong for the VC baseline;
- the obvious 2020 Virginia QL2 candidate does not cover Bremo;
- the 2019 Virginia 3DEP awards found do not include Fluvanna.

Therefore do not subtract 2016 lidar from the 2020 survey and call the result the measured six-inch excavation. The site experienced substantial excavation and reshaping between those dates.

## Status after F181

- Independent survey truth: **PASS** — frozen in F180.
- Public lidar pair matching that truth interval: **FAIL**.
- Numerical validation: **not complete**.

## Next action — F182

Screen the next realistic non-lidar historical-surface source for the same 2019-2020 interval: public/state aerial imagery or photogrammetric source data with actual stereo/elevation capability.

Gate it in this order:

1. acquisition dates bracket the VC/six-inch interval;
2. raw stereo/source imagery is actually accessible, not only an orthophoto;
3. ground sample distance / control / published vertical capability could plausibly resolve ~0.15 m;
4. coverage includes West Ash Pond.

If any one of those gates fails, close the route without running photogrammetry.

Do not use the frozen CBR-02 values to choose imagery or tune reconstruction.
