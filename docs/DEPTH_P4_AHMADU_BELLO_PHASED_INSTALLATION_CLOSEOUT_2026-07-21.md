# Depth P4 Ahmadu Bello Phased-Installation Closeout — 2026-07-21

Status: `ground_method_reference_retained_satellite_event_path_rejected_phased_installation`.

No email, form, author contact, or records request was sent.

## Result

Ahmadu Bello University Geophysics Test Site remains a strong ground-method reference with eight explicit depth-to-top values, but its whole-site Sentinel-1 pre/post route is not a clean one-event experiment.

## Newly verified phased history

The public 2024 VLF-EM article states that its study installed subsurface targets different from targets already present at ABUGTS.

The public 2024 magnetic article is more explicit:

- two targets already existed at ABUGTS;
- the study installed thirteen additional targets;
- the resulting site therefore contains targets from more than one installation event;
- excavation and restoration effects may influence the observed geophysical signal.

The publications do not expose exact dates and boundaries for each installation phase.

## Consequence

A single whole-site Sentinel-1 before/after comparison cannot be assigned to one documented burial event without separating:

```text
original_existing_targets
+ later_added_targets
+ excavation_and_surface_restoration_for_each_phase
+ exact_phase_boundaries
+ exact_phase_dates
```

Because the site is approximately 55 m by 55 m, target-level separation is already unsupported at Sentinel-1 scale. Multiple overlapping installation phases make a whole-site event comparison additionally non-identifiable.

## Retained evidence

The following remains valid for ground-method research:

- eight published `Depth to top (m)` references;
- known target materials, dimensions, positions, depths, and orientations;
- pre-burial and post-burial ground-geophysics comparisons;
- independently documented pre-burial background profiles.

The following remains missing:

- source-backed installation or survey uncertainty;
- target-placement sheets;
- exact construction dates and boundaries;
- public raw datasets and acquisition dates.

## Classification

```text
candidate = P4_AHMADU_BELLO
physical_depth_provenance = installed_known_depth
reference_definition = explicit_depth_to_top
verified_depth_record_count = 8
reference_uncertainty_m = not_reported
ground_method_research_usable = yes
confirmed_ground_background_candidate = yes_pending_raw_support
sentinel_1_target_level_separation = not_supported
sentinel_1_whole_site_one_event = rejected_phased_installation
private_pack_import_approved = no
candidate_state = method_research_only_pending_source_uncertainty
```

## Decision

Do not spend further public-only effort trying to recover one whole-site Sentinel-1 event date for P4. The public record proves that there was more than one installation phase.

P4 may return to consideration only if phase-specific construction logs, boundaries, dates, and source-backed uncertainty are obtained. Even then, any satellite experiment would require a demonstrably isolated large section, not individual targets.

## Waiting for

```text
phase_specific_target_placement_logs
+ phase_boundaries
+ phase_dates
+ original_and_added_target_map
+ source_supported_reference_uncertainty
+ raw_pre_and_post_ground_data
```

## Next step

Remove P4 from the active whole-site Sentinel-1 event queue. Retain it as ground-method depth and background evidence only. Continue with candidates that have a single documented construction event and explicit survey or installation uncertainty.

## Public references

- Alao, J. O. et al. `Depth estimation of buried targets using integrated geophysical methods: comparative studies at Ahmadu Bello University Geophysics Test Site.` Environmental Challenges 15 (2024), 100910. https://doi.org/10.1016/j.envc.2024.100910
- Alao, J. O. et al. `The effectiveness of very low-frequency electromagnetics (VLF-EM) method in detecting buried targets at a controlled site.` Discover Applied Sciences 6 (2024), 29. https://doi.org/10.1007/s42452-024-05650-6
- Alao, J. O. et al. `The studying of magnetic anomalies due to shallow underground targets and the environmental applications.` Results in Earth Sciences 2 (2024), 100016. https://doi.org/10.1016/j.rines.2024.100016
- Alao, J. O. et al. `Construction of multi-purpose geophysical test site on a lateritic clay soil.` Arabian Journal of Geosciences 17 (2024). https://doi.org/10.1007/s12517-024-12039-7
