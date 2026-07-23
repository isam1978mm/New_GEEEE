# Depth Blocker 2 - Known Data Source Screening

**Date:** 2026-07-24  
**Branch:** `main`  
**Scope:** established datasets, registries, controlled test facilities, and named research-source groups only  
**General candidate-site search:** remains closed

## Decision summary

| Source | Decision | Direct Sentinel-1 calibration status |
|---|---|---|
| Colorado School of Mines Geophysical Discovery Lab at Kafadar Commons | `method_research_only` | Not good to go |
| USACE Formerly Used Defense Sites GIS | `rejected_registry_only_and_out_of_family` | Not usable |
| National Pipeline Mapping System public data | `rejected_missing_depth_and_precision` | Not usable |
| Buto / Tell el-Fara'in 2026 Sentinel-1 + ERT + excavation study | `evidence_verified_pending_support` | Strong hold; not good to go |
| Nile Delta radar/GEE research thread led by Elfadaly, Abouarab, Elbehery and collaborators | `source_holder_lead_only` | Not a ready dataset |

None of these five sources supplies a ready multi-site Sentinel-1 depth-calibration dataset.

## 1. Colorado School of Mines Geophysical Discovery Lab

### What is real and useful

The facility is a genuine controlled geophysical test site built beneath Kafadar Commons. Public Colorado School of Mines material documents benign engineered targets with construction-known dimensions and depths, including buried walls, pipes, a dipping concrete slab, mixed-material structures, boreholes, and a buried fiber-optic array.

The public record confirms, among other examples:

- a mixed-material structure about 25 ft by 25 ft with its top about 2 ft below the surface;
- archaeological-style walls beginning about 2 ft below the surface;
- a dipping concrete slab whose top varies from about 2 ft to about 7.2 ft;
- a buried fiber-optic array covering roughly 30 m by 90 m;
- an overall field reported in later Mines research as roughly 40 m by 100 m.

These are independent construction-known references and are valuable for ground-geophysics research and controlled-method testing.

### Why it does not clear the current Sentinel-1 gate

1. **The useful buried targets are small relative to Sentinel-1 resolution.** Sentinel-1 Interferometric Wide Swath imagery has approximately 5 m by 20 m ground resolution before later GRD processing effects. A roughly 7.6 m by 7.6 m target does not provide a clean isolated satellite-scale depth sample.
2. **The site contains many different nearby buried targets and utilities.** A Sentinel-1 pixel or analysis window would mix several structures and surface influences rather than represent one known depth.
3. **The entire site is one physical group.** It cannot provide independent train, validation, and holdout groups.
4. **No public numerical placement or survey uncertainty was found.** The public descriptions give nominal or approximate construction depths, but not a defensible numerical accuracy bound for calibration intake.
5. **No documented Sentinel-1-scale confirmed-negative area was found.** Ordinary nearby grass cannot be assumed target-free because the field contains many buried structures and services.
6. **The construction period is strongly confounded.** The lab was created during major campus construction, staging, trenching, and reconstruction of the field, so a pre/post satellite change would be dominated by surface works rather than depth alone.

### Decision

```text
source_evidence_usable = yes
method_research_usable = yes
direct_app_calibration_usable = no
classification = method_research_only
```

Kafadar Commons is useful as a controlled ground-geophysics benchmark or research-method site. It is not a direct Sentinel-1 depth-calibration site under the current contract.

Do not count it toward the three required independent Sentinel-1 site groups.

## 2. USACE Formerly Used Defense Sites GIS

### What the source contains

The public GIS is a national inventory of properties, projects, and program boundaries. It is useful for program-level indexing and site status.

### Why it is not usable here

- The GIS is a boundary and project registry, not a measured depth-to-target dataset.
- Site-level depth would still require separate administrative, engineering, or investigation records.
- The relevant munitions-related records are outside the project's approved benign finding family and must not enter the active calibration pack.
- It does not provide ready confirmed negatives, uncertainty, or independent split groups.

### Decision

```text
source_evidence_usable = registry_only
method_research_usable = no_for_active_pack
direct_app_calibration_usable = no
classification = rejected_registry_only_and_out_of_family
```

Do not continue site-by-site FUDS depth searching for this project.

## 3. National Pipeline Mapping System public data

### What the public source provides

The public viewer gives general information about transmission pipelines and related facilities.

### Why it is not usable here

- The public map is not intended to identify exact pipeline locations.
- The published minimum geospatial accuracy is approximately plus or minus 500 ft, far too coarse for the required site matching.
- The public attribute set does not provide a usable depth-of-cover calibration field.
- More detailed access is restricted to eligible government and pipeline-operator users and remains limited to their jurisdiction or operations.
- Therefore it cannot provide public measured depth, uncertainty, mapped target geometry, confirmed negatives, and independent splits.

### Decision

```text
source_evidence_usable = no_for_depth
method_research_usable = no
direct_app_calibration_usable = no
classification = rejected_missing_depth_and_precision
```

## 4. Buto / Tell el-Fara'in 2026 study

### Full-text status

The Acta Geophysica paper is open access. The full text was checked, so this is no longer a `hold_pending_full_text` case.

Paper:

**Multi-scale detection of buried archaeological elements across different occupation phases: an integrated approach using radar satellite imagery and electric resistivity tomography at Buto, northwestern Nile Delta of Egypt**, Acta Geophysica 74, article 112 (2026), DOI `10.1007/s11600-026-01809-4`.

### What is independently verified

- One Sentinel-1 GRD C-band acquisition is identified exactly: **5 May 2018**, descending orbit, VV/VH, processed in SNAP.
- The Sentinel-1 analysis outlined a large oval anomaly reported as approximately **128 m by 62 m**, large enough to avoid the immediate small-target rejection that affected Kafadar Commons.
- A quasi-3D ERT survey used 15 profiles over approximately **5,400 square metres**.
- The ERT work used georeferenced control, repeat measurements, filtering, and 2D/3D inversion.
- Excavation used a georeferenced **10 m by 10 m** trench, controlled 10 cm spits, a local datum, total-station mapping, and XYZ recording.
- Excavated mudbrick walls began at reported depths of approximately **3.1 m, 3.2 m, 3.5 m, and 4.1 m** below the local ground surface in different sub-squares.
- The excavation and ERT confirmed real buried architectural material independent of the satellite interpretation.

### Important depth correction

The paper contains several different depth statements that must not be combined into one calibration label:

- approximately 3.1-4.1 m: excavated top depths of specific mudbrick walls;
- approximately 3-6 m: ERT anomaly depth range associated with architecture;
- approximately 6-7 m: interpreted artificial foundation layer;
- nearly 14 m: natural sand reached in the deepest borehole.

The nearly 14 m value is **not** an excavation-confirmed buried-feature top and is not a Sentinel-1 calibration depth.

### Why it is not good to go yet

#### Gate 1 - depth definition

The excavation gives strong depth-to-top evidence inside the 10 m by 10 m trench. However, the Sentinel-1 anomaly covers a much larger area, and the paper does not prove that one depth value applies across the full 128 m by 62 m radar footprint. The published depth variation reflects real spatial heterogeneity.

#### Gate 2 - numerical uncertainty

The paper reports ERT inversion RMS errors of approximately 1% to 2.5%, repeat stacks, and removal of measurements above an error threshold. Those values describe resistivity-data/model fit and measurement quality; they are **not a numerical uncertainty in metres for the excavated wall-top depth**.

The excavation was conducted in 10 cm spits and mapped with a total station, but the paper does not state a numerical total-station accuracy, vertical-control tolerance, or final uncertainty for the wall-top depths.

Required missing support:

- published vertical survey accuracy or total-station control tolerance; or
- the excavation XYZ/total-station data and datum-control records needed to calculate a defensible depth uncertainty.

#### Gate 3 - observation-date validity

The exact Sentinel-1 date is known, but the article does not give a sufficiently clear construction/excavation chronology to prove that the complete radar footprint was still undisturbed on 5 May 2018. The date relationship between the image, clearing, ERT campaigns, and excavation must be resolved before intake.

#### Gate 5 - confounder control

The study intentionally used a May image under dry harvest-season conditions, which is useful context. However, the radar feature is on a large archaeological mound with strong topographic, soil, moisture, vegetation, and cultural-layer variation. The paper also states that the apparent oval shape is affected by descending-orbit viewing geometry.

#### Gate 7 - confirmed negative

The paper compares the anomaly with surrounding ground, but it does not independently prove a Sentinel-1-scale target-free comparison area. Surrounding ground at a multilayered archaeological tell cannot be assumed empty.

#### Gate 8 - radar/depth linkage

The paper demonstrates a spatial association: Sentinel-1 identified a large anomaly, and ERT plus excavation confirmed buried archaeology in the investigated area. It does **not** show that Sentinel-1 backscatter varies quantitatively with known depth.

Treat the paper as evidence that Sentinel-1 can help locate a ground-truthed archaeological zone under favourable conditions, not as proof of direct C-band depth estimation to 3-6 m. The paper itself cites much shallower typical C-band penetration figures for clay and dry sand.

### Data availability

The paper includes no downloadable code, raw ERT data, excavation XYZ data, survey-control file, or supplementary calibration package. The published data-availability statement does not provide an open dataset route.

### Decision

```text
source_evidence_usable = yes
method_research_usable = yes
direct_app_calibration_usable = no_current_public_package
classification = evidence_verified_pending_support
full_text_check = complete
```

Buto is the strongest Sentinel-1-native physical-validation lead found so far. It remains a **hold**, not a pass. It may become usable only if the missing numerical depth uncertainty, observation chronology, footprint-level depth mapping, and confirmed-negative evidence are supplied.

It counts as one physical site group at most; it cannot by itself provide train, validation, and holdout.

## 5. Nile Delta radar/GEE research thread

### What the publication record shows

The overlapping Kafrelsheikh University and NARSS research group has repeatedly applied radar, optical imagery, historic maps, GEE, ground geophysics, boreholes, and excavation across the northern Nile Delta.

The public record includes:

- a 2019 Remote Sensing paper using Sentinel-1, optical imagery, and historic maps around northern Delta tells;
- a 2022 Archaeological Prospection paper using radar imagery and GEE for Burullus paleolandscape analysis;
- a 2025 Buto paper using geophysics, remote sensing, and excavation;
- the 2026 Buto Sentinel-1 + ERT + excavation paper reviewed above.

### What it does not yet provide

The related papers do not form a ready multi-site known-depth dataset:

- the 2019 work identifies several large **potential** settlement areas, but does not provide independent excavated depth-to-top labels and uncertainty for each area;
- the 2022 Burullus work is a paleolandscape and long-term change study, not a buried-feature depth calibration package;
- the 2025 and 2026 physical-validation papers concern the same Buto physical site and therefore cannot be split into independent train, validation, and holdout groups;
- no shared public repository containing excavation XYZ files, survey accuracy, confirmed negatives, and aligned Sentinel-1 acquisition records was found.

### Independence clarification

The dataset contract requires independence by **physical site/group**, not necessarily by different author teams. The same university team could provide train, validation, and holdout groups if it supplied complete evidence from genuinely separate physical sites and the split was frozen by site.

Using one research team for all sites would still create a common-method bias that should be reported and later tested with an outside holdout, but it does not automatically violate the current group-split rule.

### Decision

```text
source_evidence_usable = yes_for_source_discovery
method_research_usable = yes
direct_app_calibration_usable = no
classification = source_holder_lead_only
```

This research group is a credible **source-holder lead**, not a dataset already available for import. Do not count its publication list as multiple independent calibration groups unless separate sites have complete independent depth, uncertainty, negative, date, and sensor evidence.

## Final result

```text
known_source_screening_completed = 5
new_direct_calibration_sources = 0
strong_hold_sources = 1
method_research_only_sources = 1
source_holder_leads = 1
rejected_sources = 2
public_candidate_site_search = still_closed
depth_blocker_2 = still_blocked
```

## Best current lead

Buto / Tell el-Fara'in is the best methodological match found so far because it combines an exact Sentinel-1 acquisition, a satellite-scale anomaly, ground geophysics, controlled excavation, and measured wall-top depths.

Its first blocking item is now clearly defined:

> obtain a numerical uncertainty in metres for the excavated depth reference, together with enough raw/control data to map those depths reliably to the larger Sentinel-1 footprint.

Even if that item is resolved, a confirmed negative and at least two more independent physical sites are still required.

## What remains worth looking for

The useful source class remains:

> an established **multi-site benign controlled-test, excavation, or engineering dataset** containing measured depth to the top of buried features, numerical uncertainty, mapped geometry, dates, and independently documented no-target areas.

A named university or agency team with several separately excavated sites can qualify as a source lead. General site-by-site candidate searching remains closed.

## Sources reviewed

- Colorado School of Mines Department of Geophysics facility pages and Geophysical Discovery Lab material.
- ESA Sentinel-1 instrument documentation.
- USACE official FUDS GIS and program documentation.
- PHMSA official NPMS public-viewer and access documentation.
- Abouarab, Elfadaly, Elbehery et al., Acta Geophysica 74, article 112 (2026), DOI `10.1007/s11600-026-01809-4`.
- Elfadaly et al., Remote Sensing 11, 3039 (2019), DOI `10.3390/rs11243039`.
- Elfadaly et al., Archaeological Prospection 29, 369-384 (2022), DOI `10.1002/arp.1860`.
- Abouarab et al., Archaeological Prospection 32, 437-457 (2025), DOI `10.1002/arp.1971`.
