# Depth Controlled-Site Event-Date Recovery — 2026-07-18

Status: active evidence acquisition. This document records installation/construction dates for controlled physical sites and defines conservative pre/post screening windows. It does not approve depth estimation or evidence import.

## Purpose

A whole-site Sentinel-1 pre/post experiment requires a defensible physical event date. Publication date is not a substitute for installation date.

The event-date workflow is:

```text
recover installation or construction period
→ identify an uncontaminated pre-event period
→ exclude active excavation and restoration dates
→ identify a stable post-event period
→ verify Sentinel-1 acquisition coverage and orbit consistency
```

## Site E1 — Texas A&M University–Corpus Christi

Primary sources:

- official university project description published 2020-11-24;
- construction article DOI `10.1190/tle40030208.1`.

Verified facts:

- the controlled site measures 50 m by 50 m;
- construction occurred from February through March 2020;
- the work included a pre-installation subsurface survey, excavation, and target placement;
- the field laboratory was completed on 2020-03-04;
- targets include benign drums, buckets, pipes, and well-cover analogues at known depths.

Recovered event metadata:

```text
physical_site_group = tamucc_controlled_site
construction_start_resolution = month_only
construction_start = 2020-02
construction_complete_date = 2020-03-04
sentinel_1_mission_era = yes
pre_installation_survey_documented = yes
```

### Conservative satellite-window policy

The exact day on which each target was buried is not yet recovered. Therefore the working whole-site policy is:

```text
pre_event_window_end_exclusive = 2020-02-01
construction_transition_start = 2020-02-01
construction_transition_end_exclusive = 2020-04-01
post_event_window_start = 2020-04-01
```

Reason:

- all February and March observations are excluded from the first comparison because excavation, target placement, soil disturbance, grading, and restoration may have occurred during that period;
- `2020-03-04` remains the recorded completion date;
- the first screening uses April 2020 as the earliest post-construction month rather than pretending the exact stabilization day is known.

This is a conservative experiment policy inferred from the documented construction period. It is not a source-reported uncertainty value.

## Site E2 — Ahmadu Bello University

Primary sources include:

- DOI `10.1016/j.envc.2024.100910`;
- DOI `10.1007/s42452-024-05650-6`;
- DOI `10.1007/s44288-024-00058-6`;
- DOI `10.1007/s12517-024-12039-7`.

Verified facts:

- the studies explicitly describe a pre-burial site characterization phase;
- targets of known properties were then buried at controlled depths and locations;
- post-burial geophysical surveys were performed;
- the controlled site is 55 m by 55 m.

Current event-date status:

```text
pre_burial_measurements_confirmed = yes
post_burial_measurements_confirmed = yes
exact_calendar_installation_date = not_yet_recovered
sentinel_1_pre_post_split_date = pending
```

The absence of a calendar date does not reject the source. The next action is to inspect the construction paper and request the construction log or acquisition metadata from the authors.

## Sites without Sentinel-1 pre-installation opportunity

### TU1208 / IFSTTAR Nantes

The site was constructed in 1996. Sentinel-1 did not exist then, so it cannot support a Sentinel-1 pre-installation comparison. It remains strong independently surveyed ground-method evidence and a post-installation satellite sanity-check candidate.

### IAG/USP

The controlled site predates the Sentinel-1 mission. It remains installed known-depth evidence and method-validation material, but not a Sentinel-1 pre-installation experiment.

## Immediate execution decision

```text
first_s1_pre_post_candidate = tamucc_controlled_site
first_event_completion_date = 2020-03-04
first_pre_window_end_exclusive = 2020-02-01
first_post_window_start = 2020-04-01
construction_transition_period_excluded = yes
```

Before feature extraction:

1. create a private site polygon outside Git;
2. run the dry-run coverage checker;
3. execute the aggregate Sentinel-1 coverage query;
4. confirm acquisition counts in both pre and post periods;
5. identify comparable orbit directions and relative-orbit groups;
6. define a nearby independently screened background window;
7. keep the whole site as one physical-site group.

## Checklist

- [x] Recover the Texas A&M–Corpus Christi construction period.
- [x] Recover the official completion date: 2020-03-04.
- [x] Confirm that a pre-installation survey was performed.
- [x] Define a conservative construction exclusion interval.
- [x] Confirm Ahmadu Bello pre-burial and post-burial phases.
- [ ] Recover the exact Ahmadu Bello installation date.
- [ ] Recover the Texas A&M target-by-target installation schedule if available.
- [ ] Create private site and background polygons.
- [ ] Run aggregate Sentinel-1 coverage checks.
- [ ] Approve or reject the pre/post experiment based on actual orbit support.
