# Numerical Depth Estimation — Radar-Linkage Feasibility Execution Plan — 2026-07-26

**Branch:** `main`  
**Status:** active — explicitly reactivated by the user on 2026-07-26  
**Goal:** test whether a repeatable Sentinel-1 surface response follows known or credibly ordered cover depth before resuming broad calibration-document searching

```text
broad_candidate_search = paused
broad_document_search = paused
radar_linkage_feasibility_screen = active
feasibility_dataset_build = starting
scientific_analysis_branch = starting
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
```

## 1. Fixed scope

Run the first feasibility sequence in this order:

1. River Road Landfill;
2. Auburn McMaster Street;
3. John Sevier Bottom Ash Pond;
4. Sconondoa Street only as the substitute or additional gradient site.

Do not resume generic candidate searching during this sequence.

This is an exploratory surface-response screen. It does not create calibration truth, train a production model, calculate depth in metres, or enable app depth output.

## 2. What each site can honestly test

### River Road

Use the protected, inactive capped area as the first known-cover surface-response test.

Evidence role:

- professionally certified closure;
- minimum constructed final soil cover of 0.9144 m;
- 129 measured certification pits known to exist;
- long-term cap protection and inspection history.

Current limitation:

- individual accepted pit depths and surveyed pit locations are unreadable.

Therefore the first River Road run may test only whether the capped surface has a repeatable radar contrast against a carefully matched nearby comparison area. It cannot test a pit-by-pit depth gradient and cannot support a numerical-depth claim.

Exclude the southeast knob, drainage works, berms, riprap, roads, wells, probes, leachate or gas infrastructure, repaired areas and any later disturbance.

### Auburn McMaster

Preferred role: within-site shallow-versus-deeper cover comparison after the as-built polygons are recovered.

Evidence supports:

- a general minimum clean cover of 0.3048 m;
- a 0.6096 m ecological-buffer cover condition;
- licensed as-built surveys;
- a later vacant compacted-gravel surface;
- intact cover through May 2025.

Do not use the `>2 ft` reuse-material condition as a finite depth label. Exclude wells, utilities, recovery systems, streambank work, ecological vegetation differences and untreated background areas.

### John Sevier

Preferred role: large stable-cap independent replication.

Evidence supports:

- an actually placed 0.6096 m soil cover above the eastern geomembrane cap;
- final closure in 2017;
- a roughly 19–20 acre capped area;
- no annual geometry change or structural deficiency from 2022 through 2026;
- less than 0.1 ft movement in the latest annual inspection period.

Use only the isolated eastern cap. Exclude the active gas plant, roads, instruments, wells, drainage structures, burrows, rutting and maintenance zones. The western area may be considered only if official records and geometry establish that CCR was removed to native material and that its surface treatment is sufficiently comparable.

### Sconondoa

Use only if one of the first three sites cannot provide a valid experiment, or as an additional within-site gradient test.

Evidence supports mapped excavation depths of approximately 5–20 ft and licensed as-built surveying. Exact local depth zones remain unavailable until the survey appendix is readable. Exclude buildings, asphalt, riprap, utilities, roads, wells and the gas-regulator area.

## 3. Private input package

Detailed geometry and numeric output must remain outside Git.

For each site, the private package must contain:

```text
<site>_target.geojson
<site>_comparison.geojson
<site>_acquisition_screen.json
<site>_result.json
```

Where a real depth gradient is available, use separate shallow and deep polygons instead of a generic target and comparison polygon.

The acquisition-screen file must record, for every accepted or rejected date:

- acquisition date;
- orbit pass;
- relative orbit;
- incidence angle summary;
- rainfall and soil-moisture decision;
- vegetation or land-cover decision;
- construction or maintenance decision;
- geometry/disturbance-mask decision;
- final accepted/rejected status and reason.

No private coordinates, image IDs, local paths or feature values may be printed to the terminal or committed.

## 4. Predeclared Sentinel-1 features

Use native-resolution, physically interpretable features only:

```text
VV_dB
VH_dB
VV_minus_VH_dB
VH_to_VV_linear_ratio
incidence_angle_control
```

Incidence angle is a control, not a depth signal.

Do not use PCA anomaly scores, object-classifier labels, 2 m resampled pixels, hundreds of derived bands or post-hoc feature selection.

## 5. Acquisition matching

For every comparison:

- use IW acquisitions containing VV and VH;
- keep orbit direction fixed;
- keep relative orbit fixed within a matched series;
- require similar incidence angle;
- use repeated acquisitions, not one image;
- match season or vegetation state;
- exclude construction-active and repair periods;
- exclude dates affected by recent rainfall, flooding, snow or abnormal soil moisture;
- require enough valid native-resolution pixels to avoid single-pixel conclusions.

Preferred minimum per site:

- at least six accepted acquisitions;
- at least two seasonal windows when the surface remains comparable;
- at least four valid native-resolution pixels in every zone per acquisition;
- one fixed geometry and exclusion mask for the full matched series.

## 6. Site-level analysis

For every accepted acquisition, compute the target-minus-comparison median for the four signal features.

Record:

- sign of the contrast;
- contrast magnitude;
- valid pixel count;
- orbit and incidence-angle controls;
- temporal median and variability;
- same-direction fraction across accepted acquisitions.

A site is `site_signal_supported` only when:

1. at least two of the four signal features keep the same non-zero direction on at least two-thirds of accepted acquisitions;
2. the relationship remains after rainfall, vegetation, construction and disturbance exclusions;
3. the effect covers multiple native-resolution pixels;
4. the result is not caused by smoothing or resampling;
5. the incidence-angle control does not explain the ordering.

A one-site result remains exploratory.

## 7. Cross-site feasibility decision

The radar-depth linkage screen passes only when:

- River Road or another first site supports a predeclared relationship;
- the same direction appears at an independent second site with a different geometry and observation history;
- a site with a credible shallow/deep ordering shows the signal in the expected order;
- the relationship survives all predeclared confounder controls.

Outcomes:

```text
PASS  = repeatable direction at two independent sites, including one credible depth ordering
MIXED = repeatable surface response, but no defensible depth ordering
FAIL  = no stable relationship, reversed relationships, or confounder-driven signal
```

A pass only authorizes renewed strict document extraction. It does not enable numerical depth.

## 8. Execution order

### Step 1 — River Road setup

- prepare private target and matched-comparison polygons;
- document all excluded infrastructure and the southeast knob;
- inventory same-orbit Sentinel-1 acquisitions;
- screen rainfall, vegetation and maintenance periods;
- run the neutral feature comparison;
- write a redacted repository result.

### Step 2 — Auburn

- recover or privately derive the usable as-built subareas;
- prefer 0.3048 m versus 0.6096 m cover zones only when surface treatment is comparable;
- repeat the matched acquisition and confounder process.

### Step 3 — John Sevier

- isolate the eastern 0.6096 m cap and a source-supported comparison zone;
- use the provisionally stable 2022–2026 period;
- repeat the same features and thresholds.

### Step 4 — Sconondoa substitute

- use only after exact shallow/deep excavation zones are available;
- repeat the same fixed analysis without changing features or thresholds.

### Step 5 — Decision

- pass: resume exact evidence extraction only for the conditions that replicated;
- mixed: narrow the claim to settlement, moisture or cover-surface response;
- fail: keep numerical depth blocked and stop the Sentinel-1 GRD backscatter depth-calibration route.

## 9. Current boundary

```text
calibration_record_created = false
training_started = false
depth_measured = false
numerical_depth_ready = no
app_depth_enabled = false
```

The immediate implementation task is to add a reusable, privacy-safe multi-date runner based on the already tested Buto Sentinel-1 method screen, then execute River Road when its private geometry and acquisition-screen package are available.