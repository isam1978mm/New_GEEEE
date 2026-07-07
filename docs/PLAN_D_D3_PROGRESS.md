# Plan D D3 Progress

## Scope

Classifier feature repair for a private/local operator app. No private/local-only data was added to the repo.

## Completed

```text
D3.1 already covered: dominant_class_id uses most-common class with deterministic tie-break.
D3.3 already covered: classifier object features use valid-mask-filtered pixels.

D3.2 partial:
  - Removed classifier input-feature clamp that forced object features into [0, 1].
  - Final class_score remains bounded by the neutral classifier, but signed feature values are preserved in classifier outputs.
  - Added classifier output columns for signal_mean, signal_peak, and signal_spread.
  - Added regression coverage for negative feature values.
```

## Still open from D3

```text
D3.4 robust-scale object features against scene or local background
D3.5 replace mixed-unit features with compact vector
D3.6 keep rich private-local diagnostic labels/features without unsupported certainty
```
## Private-local policy

```text
Do not continue D3 as a public-safe neutralization track. Future classifier work should improve local diagnostic usefulness, preserve evidence detail, and avoid hiding useful operator-facing output.
```
