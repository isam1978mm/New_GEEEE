# Plan D D3 Progress

## Scope

Classifier feature repair for a private/local operator app.

This is not a public-safe neutralization track. The goal is to improve local diagnostic usefulness, preserve evidence detail, and avoid hiding useful operator-facing output.

No private/local-only data was added to the repo.

## Completed

```text
D3.1:
  - dominant_class_id uses most-common class with deterministic tie-break.

D3.2:
  - Removed classifier input-feature clamp that forced object features into [0, 1].
  - Final class_score remains bounded by the classifier, but signed feature values are preserved in classifier outputs.
  - Added classifier output columns for signal_mean, signal_peak, and signal_spread.
  - Added regression coverage for negative feature values.

D3.3:
  - classifier object features use valid-mask-filtered pixels.

D3.4 partial:
  - Added private-local object evidence fields for more useful classifier diagnostics.
  - Classifier feature inputs now use richer object/scene evidence instead of only raw mixed-unit patch means.
  - Added regression coverage for the richer private-local evidence fields.

D3.5 partial:
  - Added a compact private-local evidence vector while keeping the current classifier interface compatible.
  - Output now keeps diagnostic evidence columns so the operator can inspect why a class score changed.
Still open from D3
D3.4 remaining: inspect generated output on a real/private run and tune feature weights if needed.
D3.5 remaining: decide whether to replace the neutral classifier interface fully or keep compatibility.
D3.6 private-local labels: keep rich diagnostic labels/features, but avoid unsupported certainty.
Private-local policy
Do not continue D3 as a public-safe neutralization track.
Do not remove useful local diagnostics just because they would be sensitive in a public app.
Future classifier work should improve private/local output quality, evidence detail, and operator usability.

