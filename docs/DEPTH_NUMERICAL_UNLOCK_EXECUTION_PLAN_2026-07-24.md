# Numerical Depth Unlock Execution Plan — 2026-07-24

**Branch:** `main`  
**Status:** active  
**Broad generic search:** stopped  
**Current mechanism:** Sentinel-1 backscatter and neutral context features  
**Mining InSAR:** separate future project, not part of this unlock path

## Plain-English goal

Unlock a tested numerical **depth range** to the top of a buried reference feature.

The final output must be a range with uncertainty, not one exact guessed number.

The successful Buto method test proved only that the tested area had a repeatable spatial radar difference. It did not prove that radar measured depth.

## What is missing now

A real calibration dataset is still missing.

Buto is not yet a calibration record because it still lacks:

- a survey-grade reference footprint;
- a clear numerical uncertainty for the depth measurement;
- a confirmed no-target comparison area;
- enough separate physical sites for train, validation, and holdout.

## Minimum software floor

The validator needs three independent physical groups:

```text
train
validation
holdout
```

Each split needs at least:

- one eligible known-depth positive record;
- one eligible confirmed-no-target record.

That is a technical floor of six records.

This six-record floor is enough to prove that the data contract and split logic work. It is not automatically enough for a reliable numerical model. The pack should include as many independently measured features and useful depth values as the source records support.

## Required evidence for every positive feature

Each usable known-depth record needs:

1. exact physical site and mapped feature footprint;
2. measured depth to the **top** of the feature in metres;
3. numerical depth uncertainty or a bounded measurement interval;
4. explanation of how depth was measured;
5. source document and version;
6. construction, survey, excavation, or completion dates;
7. Sentinel-1 observation dates that can be matched to the unchanged feature;
8. target size, material or structure, soil or surface, season or moisture, and terrain information;
9. a group identifier that keeps the entire physical site in one split.

## Required evidence for every negative area

A usable negative needs independent evidence that the comparison area contains no target of the supported family.

A nearby area chosen from a map or satellite image is not enough by itself.

## Active acquisition target

### Site group 1 — Buto

Recover:

- exact surveyed anomaly and excavation footprint;
- excavation or survey depth table;
- total-station or vertical survey accuracy;
- the depth datum and definition;
- the dates of clearing, survey, ERT, excavation, and Sentinel-1 observation;
- an independently checked no-target comparison footprint;
- permission or a stable citation for using the records in a private research pack.

### Site groups 2 and 3 — separate physical sites

Obtain the same package for at least two other physical sites.

The sites may come from the same research team, but they must be physically separate and must not share one local site group across train, validation, and holdout.

## Evidence request text

Use this exact request when contacting a research group, university, agency, or project owner:

> I am building a private research calibration dataset to test whether Sentinel-1 features contain information about depth to the top of buried archaeological or engineered features. I am not asking for sensitive public release. For each physical site, I need: (1) a georeferenced footprint for the buried feature, (2) measured depth to the top of the feature, (3) the numerical survey or excavation uncertainty, (4) the measurement method and datum, (5) survey, excavation, and construction dates, (6) a georeferenced comparison area independently confirmed to contain no comparable buried feature, and (7) permission to use the records privately for research and validation. Records from three physically separate sites are especially useful because train, validation, and holdout sites must remain separate.

No outreach is performed automatically. Sending a request requires the project owner's approval and action.

## Execution order

### Phase A — Evidence intake

1. Obtain one complete Buto package.
2. Obtain two more complete physical-site packages.
3. Store all coordinate-bearing records outside Git.
4. Enter records into the private calibration pack.
5. Run the aggregate validator.

### Phase B — Relative-depth gate

1. Extract only approved neutral features.
2. Freeze train, validation, and untouched holdout site groups.
3. Fit simple preregistered relative-depth baselines.
4. Test them on the untouched physical-site holdout.
5. Require stable results and useful abstention behavior.

### Phase C — Numerical range research

Only after Phase B passes:

1. fit the median-depth baseline;
2. fit robust linear regression;
3. fit lower and upper quantile ranges;
4. preserve reference-depth uncertainty;
5. test interval coverage on the untouched holdout;
6. return `insufficient_data` for unsupported cases;
7. keep app depth output disabled until the numerical holdout gates pass.

## Current decision

```text
Buto spatial method result = successful
Buto calibration record = not ready
private calibration dataset = not populated
relative-depth fitting = blocked by missing records
numerical depth-range fitting = blocked by relative-depth gate
app numerical depth output = disabled
```

## Immediate next action

Do not run another generic search.

The immediate task is to obtain the missing Buto survey package and matching records from two additional physical sites. Until those records exist, more code cannot honestly unlock metres.
