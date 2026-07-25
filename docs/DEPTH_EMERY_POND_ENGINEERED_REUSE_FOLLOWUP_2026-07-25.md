# Emery Pond Engineered-Reuse Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** closure by removal confirmed; former pond rebuilt as an engineered liner-and-drain cleanup system  
**Calibration rows created:** 0

## Plain-English result

Former Emery Pond at Southern Illinois Power Cooperative's Marion Station was closed by removing all CCR. The public record includes a closure completion certification and a final closure report.

However, the cleared pond was not left as simple dry native ground. The independent engineering project description states that the closed pond was retrofitted with a CCR-rule-compliant composite liner system made from recompacted soil and geomembrane, together with a perimeter toe drain used to prevent liner uplift and assist groundwater cleanup.

That engineered reuse makes the surface unsuitable as a straightforward confirmed-empty comparison area for Sentinel-1 depth calibration.

## Official and independent sources checked

- Southern Illinois Power Cooperative Illinois Part 845 public document index.
- `Decontamination Certification and Closure Completion Certification Emery Pond`.
- `Emery Pond Closure Report`, formally titled `Closure and Decontamination Completion Report for Emery Pond at Marion Power Station`.
- Southern Illinois Power Cooperative annual groundwater and corrective-action reports through 2025.
- Hanson Professional Services' project description for the Emery Pond closure design and groundwater remedy.
- Illinois EPA CCR facility page identifying Former Emery Pond as an inactive closed CCR surface impoundment.

## Evidence established

```text
closure_by_removal_of_all_CCR = confirmed
closure_completion_report_exists = yes
closure_completion_certification_exists = yes
former_pond_rebuilt_with_composite_liner = yes
geomembrane_installed = yes
recompacted_soil_liner_installed = yes
perimeter_toe_drain_installed = yes
ongoing_groundwater_cleanup_function = yes
```

## Why it cannot be used as a clean comparison area

The post-removal surface includes purpose-built materials and drainage infrastructure. Radar response may therefore reflect:

- geomembrane;
- recompacted soil liner;
- drainage aggregate or toe-drain effects;
- groundwater-control conditions;
- later maintenance of the engineered remedy.

This is not equivalent to a verified dry, unused native-soil area.

The final closure-report PDF was indexed publicly, but the host repeatedly returned broken or oversized file responses. The accessible public text did not provide an extractable final survey plat, permanent benchmark coordinates, or a defensible boundary uncertainty.

Therefore:

```text
physical_CCR_removal = yes
simple_native_soil_control = no
exact_private_geometry_extracted = no
boundary_uncertainty_assigned = no
clean_unchanged_sentinel1_window = no
eligible_negative_calibration_row = no
```

## Decision

Close Emery Pond as a negative-calibration route.

Do not use the old pond boundary as a zero-target comparison polygon. Doing so would label an engineered liner-and-drain system as ordinary empty ground and could teach the model the wrong surface signal.

## Current readiness

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
calibration_records_created = 0
numerical_depth_training_ready = no
app_depth_output_ready = no
```

## Next bounded action

Inspect Illinois' inactive Pearl Ash Pond records for a readable closure survey plat, permanent benchmarks, the closure method, and post-closure surface use.

Stop that route immediately if the pond was closed in place, rebuilt with engineered systems, or lacks an exact public survey boundary.