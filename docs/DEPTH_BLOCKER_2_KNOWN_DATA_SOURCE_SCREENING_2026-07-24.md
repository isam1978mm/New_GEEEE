# Depth Blocker 2 - Known Data Source Screening

**Date:** 2026-07-24  
**Branch:** `main`  
**Scope:** named datasets, registries, test facilities, and research groups only  
**General candidate-site search:** stopped

## Plain-English decision

The broad search is over.

These sources are saved for later research. None is enough to train or release a Sentinel-1 depth model.

| # | Source | Decision | Keep for later? |
|---:|---|---|---|
| 1 | Kafadar Commons Geophysical Discovery Lab | `method_research_only` | Yes |
| 2 | USACE Formerly Used Defense Sites GIS | `rejected_registry_only_and_out_of_family` | No active use |
| 3 | National Pipeline Mapping System public data | `rejected_missing_depth_and_precision` | No active use |
| 4 | Buto / Tell el-Fara'in Sentinel-1, ERT, and excavation study | `evidence_verified_pending_support` | Yes - strongest lead |
| 5 | Nile Delta radar and Google Earth Engine research group | `source_holder_lead_only` | Yes |
| 6 | Italian buried steel-drum test site | `method_research_only` | Yes |
| 7 | FHWA SHRP2 R01B utility investigation program | `method_research_only` | Yes |
| 8 | Mining subsidence studies using Sentinel-1 InSAR | `separate_mechanism_research_only` | Yes, but outside the active depth pack |
| 9 | FERC eLibrary pipeline compliance records | `unconfirmed_source_lead_only` | Yes, as a named archive |
| 10 | State and national karst/cave databases | `dead_end_for_active_pack` | No active use |

## 1. Kafadar Commons Geophysical Discovery Lab

### What it provides

- Real buried targets built for geophysical testing.
- Construction-known depths and target dimensions.
- Benign materials such as concrete, clay, cement, metal, PVC, walls, and cable.

### Why it is not enough

- Most individual targets are too small for a clean Sentinel-1 sample.
- Many targets are close together, so the satellite signal would be mixed.
- It is one physical site, not separate train, validation, and holdout sites.
- No public numerical placement uncertainty was found.
- No documented Sentinel-1-size empty comparison area was found.
- Major construction and trenching could dominate any satellite change.

### Decision

```text
classification = method_research_only
direct_Sentinel_1_calibration = no
```

Keep it as a controlled ground-geophysics example. Do not count it as a usable calibration site.

## 2. USACE Formerly Used Defense Sites GIS

### What it provides

- A large public index of former military properties and project boundaries.

### Why it is not enough

- It is a boundary registry, not a measured depth dataset.
- It does not provide ready depth, uncertainty, confirmed negatives, or independent splits.
- Munitions-related records are outside this project's approved benign finding family.

### Decision

```text
classification = rejected_registry_only_and_out_of_family
direct_Sentinel_1_calibration = no
```

Do not continue site-by-site FUDS searching for this project.

## 3. National Pipeline Mapping System

### What it provides

- General public pipeline information.

### Why it is not enough

- The public map is not precise enough for exact site matching.
- Public data does not provide usable depth-of-cover values.
- Detailed access is restricted.
- It does not provide confirmed negatives or separate site groups.

### Decision

```text
classification = rejected_missing_depth_and_precision
direct_Sentinel_1_calibration = no
```

## 4. Buto / Tell el-Fara'in, Egypt

### What it provides

- A real Sentinel-1 image date: 5 May 2018.
- A large radar anomaly.
- Ground electrical-resistivity work.
- Independent excavation.
- Excavated mudbrick wall tops at about 3.1 to 4.1 metres below the local ground surface.

### Why it is the strongest lead

The buried feature was not guessed from the satellite image. It was checked with ground work and excavation.

### What is still missing

- A numerical uncertainty for the excavated depth values.
- A confirmed empty comparison area.
- Clear control of moisture, vegetation, ground clearing, and other surface changes.
- Proof that the Sentinel-1 signal changes with depth.
- Two more independent physical sites.

The paper supports detection and spatial matching. It does not yet prove numerical depth estimation from Sentinel-1.

### Decision

```text
classification = evidence_verified_pending_support
status = strong_hold
direct_Sentinel_1_calibration = not_yet
```

Keep Buto as the first site to use in a future method test.

## 5. Nile Delta radar and Google Earth Engine research group

### What it provides

- A real research team using radar, Google Earth Engine, ground geophysics, and archaeology across several Nile Delta locations.
- A possible route to records from more than one physical site.

### What is still missing

The published papers do not provide one ready package containing:

- measured depth with numerical uncertainty;
- confirmed empty areas;
- exact site-group separation;
- enough complete sites for train, validation, and holdout.

The sites may come from the same research team. Independence requires different physical site groups, not different authors.

### Decision

```text
classification = source_holder_lead_only
ready_dataset = no
```

Keep the group name for later. No outreach was performed.

## 6. Italian buried steel-drum test site

**Source:** Marchetti and Settimi, *Integrated geophysical measurements on a test site for detection of buried steel drums*, Annals of Geophysics, 2011.

### What it provides

- Twelve empty steel drums buried at about 4 to 5 metres.
- Construction-known placement.
- Clayey-sandy ground.
- Magnetometry, electrical resistivity tomography, and electromagnetic-induction testing.

### Important result

The magnetic and electromagnetic methods detected the drums. The electrical-resistivity result mainly detected soil changes caused by digging, rather than the drums themselves.

This supports an important warning:

> A geophysical or satellite signal may respond to excavation and disturbed soil instead of the buried target.

### Why it is not calibration data

- No Sentinel-1 data was used.
- The footprint is too small for the approved satellite experiment.
- It is one site.
- No useful numerical placement uncertainty was published for this contract.
- It does not provide a Sentinel-1-size confirmed negative.

### Decision

```text
classification = method_research_only
direct_Sentinel_1_calibration = no
```

Keep it as supporting evidence for the excavation-disturbance problem.

## 7. FHWA SHRP2 R01B - Utility Investigation Technologies

**Report:** *Utility-Locating Technology Development Using Multisensor Platforms*, SHRP2 Report S2-R01B-RW-1.

### What it provides

- A national transportation research program.
- Ground-based multichannel GPR and time-domain electromagnetic induction.
- Testing and implementation work in different soils and project settings.
- Standard procedures for collecting and processing ground-geophysical data.

### Important accuracy correction

Quality Level A utility information is commonly described as having about 15 mm vertical accuracy.

That accuracy applies when a utility is physically exposed and surveyed. It is not the accuracy of GPR, TDEMI, or Sentinel-1.

The 15 mm figure cannot be copied into this project's depth-uncertainty field for a remote measurement.

### Why it is not a ready dataset

- It is ground-based, not Sentinel-1-based.
- The report is about technology development and field procedures, not an open calibration table ready for this project.
- It does not provide a complete set of Sentinel-1-size positive and negative areas.
- It does not establish a satellite signal-to-depth relationship.

### Decision

```text
classification = method_research_only
direct_Sentinel_1_calibration = no
```

Keep it for designing proper ground truth and uncertainty procedures.

## 8. Mining subsidence studies using Sentinel-1 InSAR

### What they provide

Published mining studies often have:

- known underground mining depth from mine records;
- very large mapped working panels;
- long Sentinel-1 time series;
- non-mined or stable reference areas;
- ground surveys or models used to check measured surface movement;
- several mines or panels that may be physically separate.

This makes the literature strong for studying mining-related surface deformation.

### The important mismatch

These studies use **InSAR phase** to measure how the ground surface moves or sinks after mining.

The current project is trying to study whether ordinary Sentinel-1 backscatter features such as `VV_dB`, `VH_dB`, and simple ratios contain information about the depth of a buried feature.

These are different measurements:

```text
mining_InSAR = surface movement caused by mining
current_depth_track = backscatter or intensity differences near a buried feature
```

A strong relationship between mining depth and surface subsidence would not prove that Sentinel-1 backscatter can measure buried-feature depth.

### Scope decision

Under the current project contract, InSAR is not part of the active depth feature set. Adding it would require a separate feature pipeline, separate physical model, separate validation rules, and a deliberate project-scope change.

### Decision

```text
classification = separate_mechanism_research_only
active_depth_calibration_pack = no
keep_as_future_InSAR_track = yes
```

Keep this literature for a possible future **surface-deformation** feature, not for the current buried-feature depth model.

## 9. FERC eLibrary pipeline compliance records

### What is confirmed

- FERC eLibrary is a real public docket and filing system.
- Pipeline construction and compliance reports are filed there.
- Some dockets contain detailed construction-status and compliance attachments.

### What is not confirmed

No specific public filing has yet been verified to contain all of the following:

- a usable depth-of-cover table;
- exact mapped positions;
- numerical survey accuracy;
- dates that can be matched to Sentinel-1;
- a confirmed empty comparison area;
- enough independent sites.

Search-engine checks did not identify a specific ready filing by the phrase `depth of cover survey`.

### Decision

```text
classification = unconfirmed_source_lead_only
verified_depth_dataset = no
specific_docket_identified = no
```

Keep FERC eLibrary as a named archive for later. Do not reopen broad docket-by-docket searching now.

## 10. State and national karst/cave databases

### What is available

The USGS national karst database maps rock areas where karst may exist or develop.

### Why it is not enough

It does not provide a national table of:

- individual cave or void locations;
- measured depth to each cave ceiling;
- numerical uncertainty;
- confirmed no-void comparison borings;
- dates and geometry suitable for Sentinel-1 matching.

### Decision

```text
classification = dead_end_for_active_pack
direct_Sentinel_1_calibration = no
```

Do not spend more time on national karst maps for this blocker.

## Final result

```text
sources_screened = 10
strong_hold_sources = 1
source_holder_leads = 1
unconfirmed_archive_leads = 1
method_research_sources = 3
separate_mechanism_tracks = 1
rejected_or_dead_end_sources = 3
ready_multi_site_depth_datasets = 0
general_web_search = stopped
outreach_performed = false
```

## What may proceed later

### Buto method test

- reproduce the published Sentinel-1 observation;
- compare it with the known excavation area;
- check whether a stable satellite-scale anomaly exists;
- report detection or spatial agreement only;
- do not claim that Sentinel-1 measured the wall depth.

### Separate mining-InSAR study

This may be planned only as a different surface-deformation project. It must not be mixed into the current buried-feature depth calibration pack.

## What may not proceed yet

- depth-model training;
- numerical depth prediction;
- app depth output;
- claims that radar intensity directly measures depth.

## Saved-for-later list

Keep these active references:

1. Buto as the strongest Sentinel-1 plus excavation case.
2. The Nile Delta group as a possible holder of more complete site records.
3. The Italian steel-drum paper as evidence that digging disturbance can create the signal.
4. SHRP2 R01B as guidance for ground truth and uncertainty handling.
5. Mining InSAR as a separate future surface-deformation track.
6. FERC eLibrary as an unconfirmed archive lead.

No further broad source search is planned.

## Main sources reviewed

- Colorado School of Mines Geophysical Discovery Lab material.
- USACE FUDS program and GIS documentation.
- PHMSA NPMS public-viewer documentation.
- Abouarab, Elfadaly, Elbehery and collaborators' Buto study and related Nile Delta papers.
- Marchetti and Settimi, Annals of Geophysics, 2011.
- National Academies SHRP2 Report S2-R01B-RW-1.
- FHWA Subsurface Utility Engineering guidance.
- Published Sentinel-1 InSAR mining-subsidence studies.
- FERC eLibrary public docket records.
- USGS national karst map and database documentation.
