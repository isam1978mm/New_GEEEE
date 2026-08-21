# Depth External-Elevation Session Handoff — 2026-08-21 — after F175

## 1. Purpose

This is the controlling handoff for the next session.

Current scientific goal:

> Find an independent measured elevation/depth reference that can validate numerical depth without using known Tyrone TP5/TP6/TP7 answers to select, fit, tune, shift, or rescue the result.

The Tyrone direct-elevation repair remains blocked at Step 4, so this session tested external sites where real pre/post construction survey surfaces may exist.

## 2. Hard constraints — do not change

- Do **not** change the classifier.
- Do **not** change the UI unless explicitly requested.
- Do **not** change the NB formula unless explicitly requested.
- Do not claim numerical depth is validated without an independent/unseen measured reference.
- Always distinguish measured depth, calibrated estimate, raw NB proxy, and volume-derived average thickness.
- Do not use known Tyrone TP5/TP6/TP7 depths to decide whether a remote-sensing or survey candidate is accepted.
- Do not restart closed Tyrone Step-4 public-data searches.
- Do not enable the failed scalar-interpolation route.
- Route A / EMNRD application verification remains separate and should not be substituted without explicit user direction.
- Main local backend port remains 8007, not 8000.

Frozen historical-surface gate remains:
- RMSEz <= 0.15 m
- abs median vertical residual <= 0.05 m
- 95th-percentile abs vertical residual <= 0.30 m
- residual-plane drift <= 0.10 m across target footprint

## 3. Working method expected by the user

Keep each step short and explicit:

- **What I’m doing now**
- **Current status**
- **Next**

Do not silently stop. Do not loop on already-closed searches. If a route closes, say so plainly and move to the next exact action.

## 4. Tyrone status entering this handoff

Tyrone Step 4 target remains:

> an independent post-grading / pre-cover Dam 3X surface from roughly Sep 2004 through Apr 2005.

Public/project-available Step-4 search was already exhausted in F161.

Remaining realistic Tyrone source is an unpublished/internal construction record, primarily from:
1. Freeport-McMoRan / Tyrone technical-engineering archive
2. M3 Engineering project archive 03141.01
3. WSP legacy Golder archive only after the first two

The exact record specification is already documented in F162.

Do **not** repeat F34–F162.

## 5. F174 — Bremo West Ash Pond result

Controlling file:

`docs/DEPTH_BREMO_F174_VOLUME_LIDAR_RESULT_2026-08-21.md`

Merged in PR #143.
Merge commit:

`18925b3036b1595658f62d41cb43346e965b3bce`

What was established:

- A real H&B Surveying & Mapping **June 9, 2016 pre-excavation field survey** existed for West Ash Pond.
- A later Dominion closure plan contains a real **July 6, 2017 H&B surveyed pond-bottom surface** and says the topography represents the bottom of pond.
- The later plan also shows a **50 ft x 50 ft pre/post excavation survey grid**.
- Excavation chronology: initial CCR excavation ran Jul 2016–Jul 2017, then paused; later work resumed in Sep 2019.
- Official records report **327,323 yd3** initial CCR removal over approximately **17 acres**.
- Volume/area normalization gives about **3.64 m (11.93 ft)** mean thickness, but this is **volume-derived**, not a measured survey depth anchor unless the quantity method is proven survey-to-survey.
- The public 2014 Central Virginia lidar shortcut was tested and **does not cover Bremo**.
- Virginia DEQ lists West Pond construction-report parts publicly, but direct retrieval was blocked in this environment.

Bremo status:

> **OPEN BUT ACCESS-BLOCKED.**

Missing artifact:

> the June 9, 2016 H&B pre-excavation surface/grid itself, or a public CQA/as-built sheet reproducing it numerically.

Do not call 3.64 m a measured depth.

## 6. F175 — John Sevier result

Controlling file:

`docs/DEPTH_JOHN_SEVIER_F175_ACCESS_RESULT_2026-08-21.md`

Merged in PR #144.
Merge commit:

`891581d2a5df2bb867fe2532489e61c5da04f694`

What was established:

- John Sevier has a valid **pre-work 2014 TVA LiDAR/topography** source.
- TVA explicitly says its CCR inventory calculation compared:
  - a native surface derived from geotechnical boring data, and
  - a **subgrade surface established by the as-built survey**.
- Therefore the post-excavation as-built survey is real and was used quantitatively.
- TVA's History of Construction names two exact reports:
  1. `Construction Certification Report, Bottom Ash Pond Pre-Closure Project — March 2017`
  2. `Construction Certification Report, Bottom Ash Pond Final Closure — July 2017`
- The History of Construction says Appendix D contains record drawings from the Pre-Closure and Final Closure projects.
- TVA inspection records also reference:
  - drawing `10W522-04` dated 11/4/2016
  - a Phillips & Jordan stacking-area survey dated 9/23/2016
- Those extra records prove real construction surveys existed but do not by themselves provide a clean excavation-bottom depth surface.
- TVA's published **0–38 ft ash depth** is explicitly estimated and must **not** be used as measured validation truth.
- Direct attempts to retrieve the large History-of-Construction Appendix D / record drawings timed out, and the exact certification reports/drawing were not separately exposed in current public search results.
- Simple pre-work versus final-surface subtraction is unsafe because CCR and soil were moved and fill was used during grading.

John Sevier status:

> **OPEN BUT ACCESS-BLOCKED.**

Science status:
- pre-work surface: PASS
- post-excavation survey existence: PROVEN
- numerical post-excavation surface: NOT RECOVERED

Missing artifact:

> the actual as-built subgrade survey / record drawing geometry, preferably from Appendix D or the March/July 2017 certification reports.

## 7. External inbox status checked this session

The inbox was checked after F175.

Result:
- **No reply from M3**
- **No reply from Freeport-McMoRan**
- A new EMNRD acknowledgment exists for a separate IPRA request received Aug 19, but it is only a receipt/processing notice, not responsive records.

Do not claim any external reply has unblocked Tyrone.

## 8. Exact point where this session stopped

After F175, the next task had begun:

> Recover the **exact remaining site names from the previous external-site audit** before starting F176.

This is important because the next session must **not invent a candidate site** or restart a generic broad search.

The attempt to recover those names from repo history had only just started when the user requested the handoff.

## 9. Exact next action for the next session

### F176 — recover the remaining audited candidate list, then test the strongest one

1. Search repo documentation/history for the earlier external depth/elevation candidate audit.
2. Extract the exact remaining candidate site names and their prior rejection/open reasons.
3. Exclude Bremo and John Sevier from repeat work unless a genuinely new survey file/source appears.
4. Pick the strongest remaining candidate that can plausibly provide:
   - correct before/after timing,
   - spatial coverage,
   - actual measured/surveyed geometry,
   - enough accuracy for the frozen 0.15 m vertical gate.
5. Test that candidate one gate at a time.
6. Persist the F176 result in the repo before moving on.

If no remaining audited site survives the geometry/access gate, state that external elevation validation is also exhausted on current public evidence rather than launching another random broad technology search.

## 10. Important documents to read first

Read these before doing new work:

1. `docs/DEPTH_EXTERNAL_ELEVATION_SESSION_HANDOFF_2026-08-21_F175.md` — this file; controlling handoff
2. `docs/DEPTH_BREMO_F174_VOLUME_LIDAR_RESULT_2026-08-21.md`
3. `docs/DEPTH_JOHN_SEVIER_F175_ACCESS_RESULT_2026-08-21.md`
4. `docs/DEPTH_TYRONE_F161_STEP4_EXHAUSTION_AUDIT_2026-08-20.md`
5. `docs/DEPTH_TYRONE_F162_CUSTODIAN_RECORD_SPEC_2026-08-20.md`
6. `docs/DEPTH_TYRONE_SESSION_HANDOFF_2026-08-20_V2_F153.md`
7. `docs/DEPTH_TYRONE_CONTINUITY_LOCK_2026-08-20_V3_F100_F152_CHECKPOINT.md`

## 11. Bottom line

At handoff:

- **Tyrone Step 4:** blocked on unpublished/internal construction record.
- **Bremo:** scientifically promising, blocked on missing June-2016 pre-excavation H&B survey geometry.
- **John Sevier:** scientifically promising and stronger on provenance, blocked on access to actual as-built subgrade record drawings.
- **M3/Freeport:** no reply as of the latest inbox check.
- **Numerical depth validation:** still not complete.
- **Next:** recover exact remaining audited candidate names and perform F176 on the strongest real candidate. Do not guess a new site.