# F183 — Bremo NAIP timing screen

Date: 2026-08-21

## Purpose

Test USDA National Agriculture Imagery Program (NAIP) as the next public aerial source after the VBMP timing failure in F182.

## Virginia NAIP acquisitions found

Official NOAA/USDA catalog records show:

### 2018 Virginia NAIP

- statewide Virginia coverage;
- acquisition time frame: 2018-08-27 through 2018-12-19;
- orthorectified aerial imagery.

### 2021 Virginia NAIP

- statewide Virginia coverage;
- acquisition time frame: 2021-04-26 through 2021-09-27;
- 60 cm GSD product;
- the NAIP acquisition cycle is generally a minimum three-year refresh.

The public catalog screen did not identify a Virginia 2019 or 2020 NAIP statewide acquisition between those two cycles.

## Required interval

The Bremo measured thickness truth corresponds to the Visual Clean -> six-inch over-excavation work during the resumed closure period from approximately late September 2019 through January 30, 2020.

## F183 decision

**FAIL at timing gate.**

The public Virginia NAIP sequence found is 2018 -> 2021, so it does not bracket the late-2019/early-2020 excavation interval.

Do not difference 2018 and 2021 NAIP-derived surfaces and interpret the result as the measured six-inch excavation. The interval is too broad and contains unrelated site changes.

Because timing fails, no stereo/vertical-accuracy work is justified for NAIP in this validation path.

## Status after F183

- measured Bremo survey truth: PASS;
- public lidar pair: FAIL;
- VBMP aerial pair: FAIL;
- NAIP aerial pair: FAIL.

## Next action — F184

Before declaring the Bremo external-surface route exhausted, inspect the DEQ CQA package and related public closure records for a **contractor/source survey deliverable** beyond the plotted Appendix A sheets — for example a point table, CAD filename, survey data file reference, earthwork report, electronic surface, or second report part that could expose the original Flora VC and over-excavation surfaces numerically.

This is now stronger than launching another broad imagery search because the CQA report proves those exact survey surfaces existed.
