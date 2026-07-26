# Numerical Depth Estimation — Radar-Linkage Feasibility Screen Decision — 2026-07-26

**Branch:** `main`  
**Goal:** determine whether Sentinel-1 contains any repeatable depth-related surface signal before continuing the expensive calibration-document search  
**Current numerical-depth status:** blocked  
**Usable calibration rows:** `0`  
**App numerical depth enabled:** no

---

## 1. Decision

Pause the broad search for more perfect calibration sites.

More than 400 candidate leads have now been screened. Most failed because one or more required evidence pieces were missing:

- actual measured depth;
- numerical uncertainty;
- exact mapped geometry;
- a clean observation period;
- an unchanged surface;
- an independently confirmed comparison area;
- enough independent site groups for train, validation and holdout.

This repeated failure is now evidence that the current work order is inefficient.

The project has been spending most effort on the expensive documentation gates before answering the cheaper and more fundamental question:

> Does Sentinel-1 show any repeatable, confounder-controlled surface response that tracks known cover depth at all?

The next phase must answer that question first.

---

## 2. Why the work order is changing

Sentinel-1 C-band does not directly measure a buried interface one to several metres below ground.

Any depth-related relationship must be indirect, through surface effects such as:

- differential settlement;
- drainage and moisture differences;
- vegetation response;
- surface roughness;
- compaction;
- long-term deformation.

This creates a serious experimental problem.

At most landfill, remediation and closure sites, changing cover depth also changes grading, soil material, compaction, vegetation, drainage and roughness. Those surface changes can dominate the radar signal.

Therefore, even a perfect depth document may not produce a usable depth model unless the radar relationship survives control for those confounders.

---

## 3. What this decision does not mean

This decision does **not** declare numerical depth impossible.

It does **not** weaken the final calibration standard.

It creates a separate exploratory phase that is deliberately ineligible for production calibration.

Exploratory records may use:

- approximate but credible depth ordering;
- source-supported minimum or bounded depth values;
- incomplete uncertainty;
- one-site within-site comparisons;
- known proxy labels.

These records must remain clearly separated from calibration truth and must never enable the app's numerical-depth output.

---

## 4. New immediate objective

Run a bounded radar-linkage feasibility screen using the strongest existing imperfect candidates.

Initial candidate bank:

1. **River Road Landfill**
   - 129 physical certification pits;
   - surveyed pit locations;
   - pit-by-pit final cover thickness records exist;
   - deficient areas were corrected and rechecked;
   - exact pit forms and measurement uncertainty remain inaccessible.

2. **Auburn McMaster Street**
   - licensed construction surveys;
   - actual local cover thickness recorded on as-built drawings;
   - mapped cover geometry;
   - later vacant condition and intact cover;
   - exact readable local values and survey accuracy remain missing.

3. **John Sevier Bottom Ash Pond**
   - documented constructed 24-inch soil cover;
   - large simple capped footprint;
   - stable inspection period from at least 2022 through 2026;
   - exact surveyed cap polygon and construction tolerance remain missing.

4. **Sconondoa Street former MGP**
   - mapped excavation-depth variation;
   - licensed as-built survey package exists;
   - later vacant condition;
   - public survey appendix remains inaccessible.

Other candidates may be added only when they provide a useful within-site depth contrast and a sufficiently simple surface.

---

## 5. Preferred experimental design

Prefer a **within-site depth gradient** over cross-site depth comparison.

A within-site design holds many confounders approximately constant:

- soil and regional geology;
- climate;
- rainfall history;
- radar orbit;
- incidence angle;
- seasonal timing;
- broad land cover;
- local construction history.

Target examples:

- one large capped area with multiple documented cover depths;
- one structure with a longitudinal depth-of-cover profile;
- one reclaimed cell with shallow and deep mapped zones;
- one corridor where depth varies systematically while surface treatment stays similar.

Preferred source classes for later screening:

- cut-and-cover tunnels;
- covered or buried municipal reservoirs;
- large transmission mains with depth-of-cover surveys;
- OSMRE AMLIS mine-reclamation records;
- USACE confined disposal facilities;
- dredged-material placement cells with before-and-after surveys.

---

## 6. Feasibility-screen inputs

The first screen should use only physically interpretable and predeclared features.

Required Sentinel-1 controls:

- same orbit direction;
- same relative orbit where possible;
- similar incidence angle;
- matched seasonal windows;
- rainfall and soil-moisture screening;
- repeated dates rather than one image;
- exclusion of construction-active periods;
- exclusion of repaired or disturbed subareas;
- geometry large enough to contain multiple native radar-resolution elements.

Initial feature set:

- VV backscatter;
- VH backscatter;
- VV minus VH or equivalent polarization relationship;
- temporal median;
- temporal variability;
- persistent moisture-sensitive contrast;
- stable spatial contrast against matched within-site control zones;
- deformation or coherence only where suitable SLC/GSLC products exist.

Do not use hundreds of unconstrained derived features in the first test.

Do not use the notebook's 2 m resampled grid as if it contains independent 2 m radar observations.

---

## 7. Test question

The screen asks one narrow question:

> After controlling for known surface and acquisition confounders, do deeper and shallower documented zones maintain a consistent radar ordering across repeated dates?

Examples of acceptable exploratory outcomes:

- deeper zones repeatedly show higher or lower median VV under matched dry conditions;
- deeper zones show a repeatable moisture-persistence difference;
- deeper zones show a consistent long-term settlement or deformation response;
- no repeatable relationship survives confounder control.

The first screen does not fit a production depth model.

---

## 8. Passing criteria

The feasibility screen passes only if all of the following are true:

1. A predeclared radar relationship is observed within a site.
2. The relationship repeats across multiple matched dates.
3. The relationship remains after excluding rainfall, vegetation and construction-active periods.
4. The same direction of relationship appears at a second independent site or structure.
5. The effect is spatially larger than isolated single-pixel noise.
6. The result is not created only by resampling, smoothing or post-hoc feature selection.

A promising but one-site-only result remains exploratory.

---

## 9. Failure criteria

The Sentinel-1 depth route should remain blocked if:

- no consistent relationship appears;
- the relationship reverses across dates;
- the signal disappears after moisture or vegetation control;
- the effect exists only during construction;
- the effect is confined to isolated pixels;
- the result cannot repeat at an independent site;
- depth performs no better than surface-condition variables alone.

A negative result across several correctly designed gradients should stop the unbounded document search for Sentinel-1 backscatter depth calibration.

---

## 10. What would unblock the app

A feasibility pass does not immediately enable numerical depth.

It only justifies returning to strict calibration evidence.

The app can expose numerical depth only after:

1. a repeatable depth-related radar relationship passes the feasibility screen;
2. strict calibration rows contain actual measured depth and uncertainty;
3. exact geometries are available;
4. observation-date validity is proven;
5. train, validation and holdout groups are independent;
6. performance is acceptable on untouched holdout sites;
7. uncertainty and out-of-distribution rejection are implemented;
8. the output is clearly described as an indirect surface-response-based estimate.

Until then:

```text
app_depth_enabled = false
calibration_record_created = false
training_started = false
numerical_depth_ready = no
```

---

## 11. Likely product outcomes

Possible final outcomes, from most to least realistic:

1. **Depth-related surface-response class**
   - shallow / moderate / deep;
   - confidence level;
   - restricted to validated surface and climate conditions.

2. **Approximate numerical depth range**
   - only for well-matched sites;
   - wide uncertainty interval;
   - strong out-of-distribution rejection.

3. **General numerical depth in metres for arbitrary locations**
   - currently considered unlikely with Sentinel-1 GRD alone.

Do not display false precision such as `2.37 m` unless independent calibration and holdout evidence support that precision.

---

## 12. NISAR / L-band track

NISAR should be treated as a separate forward-looking research track.

Potential value:

- longer wavelength than Sentinel-1 C-band;
- improved sensitivity to vegetation structure and surface deformation;
- stronger basis for repeated InSAR-style settlement monitoring;
- free public data beginning in 2026.

Limits:

- no historical pre-2026 archive for old closures;
- still not direct metre-scale underground imaging;
- requires a new SLC/GSLC or interferometric processing branch;
- cannot be added honestly as another derived feature in the current GRD notebook.

NISAR may improve future closure and reclamation monitoring but does not automatically solve historical numerical depth.

---

## 13. Required implementation order

### Phase 1 — Freeze broad candidate search

- keep all existing candidate dossiers;
- do not discard River Road, Auburn, John Sevier or Sconondoa;
- stop screening generic candidate number 401 unless it directly serves the feasibility design.

### Phase 2 — Build the exploratory dataset

- select two or three strongest within-site gradients;
- define shallow, intermediate and deep zones from available records;
- mark all records as research-ineligible calibration proxies;
- define exclusion masks for construction, roads, drainage, repairs and vegetation differences.

### Phase 3 — Build a small scientific analysis branch

- use native-resolution Sentinel-1 features;
- use matched dates and orbit controls;
- record all acquisition IDs and weather-screening decisions;
- produce transparent tables and plots;
- avoid PCA-driven target discovery and post-hoc classifier labels.

### Phase 4 — Make the decision

- pass: resume exact-document extraction only for conditions that showed repeatable linkage;
- fail: keep numerical depth blocked and stop the Sentinel-1 backscatter calibration route;
- mixed: narrow the app claim to settlement, moisture response or depth class under limited conditions.

---

## 14. Current status and next step

Current status:

```text
broad_document_search = paused
radar_linkage_feasibility_screen = approved_next_phase
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
```

Next step:

> Build the bounded feasibility-screen execution plan using River Road, Auburn and John Sevier as the first candidate set, with predeclared features, matched-date rules, confounder masks and pass/fail criteria.
