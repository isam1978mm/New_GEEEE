
  Headline finding first: Stage 1's impressive-looking numbers (0.93 PR-AUC, 0.905
  precision) are mostly a prevalence artifact. The Stage 1 positive class is
  {strong_long, strong_short} (backend/app/core/stage1_model.py:6), and those classes
  make up 3,021 of 3,490 rows = 86.6% of the data. A no-skill classifier that always
  says "valid setup" scores PR-AUC ≈ 0.866 and precision 0.866 by construction. Stage
  1's real lift is roughly +0.06 PR-AUC and +0.04 precision over doing nothing, while
  giving up 17 points of recall. The holdout fold makes this vivid: 49 positives, 1
  negative, zero true negatives
  (artifacts/scoped_retrain_after_fold_design_revision_run.json). The artifact's "beats
  baseline" flags compare against the Gate 3 floor thresholds (0.30 precision / 0.50
  recall), not against prevalence — which flatters Stage 1.

  ---
  Current State (Q1, plain English)

  What was built. A disciplined, gated research pipeline for SUI/USDT 15m spot signals:
  triple-barrier labeling (profit 1.5 ATR, risk 0.75 ATR, 12-bar horizon —
  backend/app/core/labeling.py:84-120), a Stage 1 binary "setup validity" model, a
  Stage 2 direction model, expanding walk-forward validation (69 folds × 50 validation
  rows), SHAP stability checks, baseline comparisons, and an exemplary
  scope-lock/artifact-decides governance process.

  What failed. Stage 2 direction accuracy = 0.343 — not just weak but anti-predictive:
  among strong-labeled rows, ~66% are short, so even constant-"short" would score far
  higher, and the artifact's own baseline was 0.50. SHAP top-10 stability stayed
  unstable (mean overlap 0.657, 12 unstable fold pairs) even after the fold-size fix.
  The label-revision diagnostic found no single safe repair axis.

  What was killed. The current Stage 2 direction-model path as a promotion candidate
  (docs/kill-current-stage2-model-path-result-decision.md). Model promotion, runtime
  pointer updates, threshold tuning, and all production/advisory behavior remain
  unauthorized.

  What remains useful. (a) The infrastructure: labeling engine, walk-forward harness,
  feature pipeline, artifact/report discipline — all reusable. (b) Stage 1 evidence as
  a research record of what a setup-validity classifier does on this window — preserved
  by the latest diagnostic
  (artifacts/stage1_only_setup_validator_research_first_run.json, decision
  preserve_stage1_for_research, dated today). (c) A clean negative result on Stage 2
  direction.

  What is forbidden now. Stage 1 runtime behavior, Telegram/dashboard dispatch,
  production advisory, model promotion, runtime pointer updates, threshold tuning,
  Stage 2 revival without a brand-new redesign scope, and any
  feature/label/triple-barrier changes under the current lock.

  Source of Truth

  One discrepancy to flag: docs/stage1-research-evidence-preservation-handoff.md does
  not exist. The actual chain is:

  1. docs/kill-current-stage2-model-path-result-decision.md — Stage 2 killed
  2. docs/next-product-direction-result-decision.md — direction = Stage 1 research only
  3. docs/stage1-only-setup-validator-research-scope-lock.md — the active scope lock
  4. artifacts/stage1_only_setup_validator_research_first_run.json — verdict
  DIAGNOSTIC_COMPLETE, decision preserve_stage1_for_research, recommended next gate =
  stage1_research_evidence_preservation_result_decision — this result-decision doc has
  not been written yet. That is the open procedural item regardless of which path you
  choose.

  Underlying evidence: artifacts/scoped_retrain_after_fold_design_revision_run.json and
  artifacts/feature_label_revision_after_fold_design_run.json.

  Real Blockers (Q2)

  Data blockers — the dominant category:
  - 36.6 days of data. The entire evidence base spans 2026-03-14 → 2026-04-19: one
  asset, one timeframe, one regime (56.9% strong_short — a down-skewed window). The
  diagnostic's "narrow window" check only requires ≥200 rows, so it never flagged this.
  No conclusion about edge — positive or negative — can come from five weeks.
  - ~3,490 labeled rows is far too few for 30+ features with LightGBM; the SHAP churn
  is the expected symptom of fitting noise, not a fixable modeling bug.
  - Overlapping labels: each label looks 12 bars ahead, so adjacent rows share outcome
  windows — effective sample size is much smaller than 3,490.

  Modeling blockers:
  - Stage 1's target is nearly degenerate (86.6% positive). Semantically it predicts
  "price will move ±1.5 ATR in some direction within 3 hours" — volatility
  continuation, which is well-known to be predictable and unmonetizable without
  direction. Direction is exactly what failed.
  - Stage 2 at 0.343 against a ~0.50–0.66 trivial baseline indicates the model
  anti-learned, the classic signature of regime flip inside a short window.

  Validation blockers:
  - No purge/embargo at fold boundaries. Folds use train_end = valid_start, but the
  last 12 training rows' labels are computed from price inside the validation window.
  The artifact says lookahead_leakage_possible = false, but that flag doesn't cover
  this. The leakage direction inflates results — Stage 1's already-thin lift is, if
  anything, overstated.
  - Baseline comparisons use gate thresholds, not prevalence/majority-class baselines.
  - Known v1 limitation: intrabar barrier ordering is approximate, and the
  strong-before-weak check order (labeling.py:104-120) biases labels toward "strong,"
  inflating Stage 1's prevalence further.

  Product/scope blockers: Every runtime/advisory path is locked off. Nothing currently
  authorized can ship anything — by design.

  Business/trading-edge blockers — the deepest one:
  - There is no transaction-cost model anywhere in the repo. I checked — no fee,
  slippage, or commission logic exists in the evaluation chain. With 15m bars, the
  profit target is ~1.5 ATR (plausibly 0.3–0.8% on SUI) while a Binance spot round trip
  costs ~0.2% in fees alone plus spread/slippage. Costs would consume a large fraction
  — possibly all — of the gross edge even if direction prediction worked. The project
  has never measured the one thing that determines whether it should exist.

  Core Question (Q3)

  Your proposed question — "Does any exploitable edge exist in the data after realistic
  costs, using walk-forward out-of-sample testing?" — is the right question, but it
  needs two sharpening amendments, because as stated it's unanswerable with the current
  dataset:

  ▎ "On multi-regime SUI/USDT history (≥12–18 months, not 5 weeks), does any
  ▎ pre-registered signal family — deterministic rules first, ML only if warranted
  ▎ later — produce positive net expectancy after fixed, realistic Binance spot costs,
  ▎ under purged walk-forward evaluation?"

  The amendments: (1) the data window must expand first — Binance's public klines API
  provides years of SUI/USDT 15m history for free, so this blocker is cheap to remove;
  (2) deterministic before ML — if no simple rule family survives costs, a 30-feature
  LightGBM on the same features won't either, and testing rules first avoids the
  overfitting trap entirely.

  And one honest framing note: everything measured so far has been label classification
  accuracy, which is a proxy. Expectancy after costs is the actual money question, and
  it has zero data points against it — in either direction.

  Options (Q4)

  Option: Close out as research artifact
  Goal: Honest archive; stop spend
  Effort: Low (docs only)
  Risk: Records "no edge" conclusion the evidence can't actually support — only "this
    model on 5 weeks failed" is supported
  Passes if: n/a — terminal
  Fails if: n/a
  Allowed now?: Yes (write the pending result-decision doc, then a close-out doc)
  ────────────────────────────────────────
  Option: Edge-existence study (cost-adjusted, expanded data, deterministic)
  Goal: Answer the money question once, pre-registered
  Effort: Medium (~data fetch + expectancy harness + report; the walk-forward/labeling
    infra already exists)
  Risk: Could still fail to find edge (likely); main risk is criteria drift after
  seeing
    results — must pre-register
  Passes if: ≥1 pre-registered family shows positive net expectancy with regime
    consistency
  Fails if: No family survives costs → archive
  Allowed now?: Needs new scope lock (the kill decision explicitly requires one; it's
    procedurally compatible)
  ────────────────────────────────────────
  Option: Preserve Stage 1 as offline archive
  Goal: Keep evidence retrievable
  Effort: Trivial
  Risk: None — but it's a filing action, not a path
  Passes if: Already decided by today's artifact
  Fails if: n/a
  Allowed now?: Yes — it's the artifact's recommended next gate; do it regardless
  ────────────────────────────────────────
  Option: Deterministic baseline research (standalone)
  Goal: Test simple rules vs ML
  Effort: Medium
  Risk: On 5 weeks of data it inherits every data blocker; only sensible inside the
  edge
     study
  Passes if: Rule beats cost hurdle OOS
  Fails if: No rule does
  Allowed now?: Needs new scope lock; redundant — fold into the edge study
  ────────────────────────────────────────
  Option: Data-quality/observability-only
  Goal: Better instrumentation
  Effort: Medium
  Risk: Polishing telescopes with no star to look at — improves measurement of a
  dataset
    already known to be too small
  Passes if: n/a
  Fails if: n/a
  Allowed now?: Rejected by the next-product artifact; would need a new lock; not
    justified alone
  ────────────────────────────────────────
  Option: New Stage 2 redesign from scratch
  Goal: New direction model
  Effort: High
  Risk: Repeats the failure: same 5 weeks, same cost-blindness, same overlapping
  labels.
    Premature before edge existence is established
  Passes if: —
  Fails if: —
  Allowed now?: Needs brand-new redesign scope; not recommended now
  ────────────────────────────────────────
  Option: Stop the project
  Goal: Zero further spend
  Effort: Zero
  Risk: Leaves the core question permanently unmeasured; the cheap decisive experiment
    was never run
  Passes if: n/a
  Fails if: n/a
  Allowed now?: Yes

  Recommended Next Move (Q5)

  Run one final, pre-registered, cost-adjusted edge-existence study — then stop if it
  fails. Honestly weighed against "stop and archive now," and this wins on one decisive
  consideration:

  Stopping now would close the project on a conclusion the evidence cannot support.
  What you have proven is "this two-stage ML design, on 36 days of one regime, without
  cost modeling, fails." That is not "no edge exists." The single experiment that would
  justify a confident close-out — multi-regime history, fixed realistic costs, purged
  walk-forward, simple pre-registered rules — was never run, and it is the cheapest
  experiment in the whole program: free data, existing labeling/walk-forward
  infrastructure, no model training required. Conversely, my honest prior is that the
  study will likely fail — 15m TA-derived signals on a liquid spot pair facing
  ~0.2–0.3% round-trip costs is among the most thoroughly mined and arbitraged spaces
  in existence. But that's exactly why it should be run as a kill experiment: it
  converts "we gave up" into "we measured, and the answer is no," and in the unlikely
  event something survives, you have a real foundation for the first time. One study,
  hard kill criteria, then archive. Not "manual go/no-go first" — there is nothing for
  a human to eyeball that substitutes for the expectancy number, and manual review
  reintroduces expectation-driven decisions your process correctly forbids.

  Procedural first step either way: write
  docs/stage1-research-evidence-preservation-result-decision.md to close the open gate
  (today's artifact names it as the recommended next gate), recording
  preserve_stage1_for_research as offline archive.

  Proposed Scope Lock (Q6)

  - Name: cost_adjusted_edge_existence_study_scope_lock
  - Purpose: Determine, once, whether any pre-registered deterministic signal family on
  expanded multi-regime SUI/USDT 15m history produces positive net expectancy after
  fixed realistic costs under purged walk-forward evaluation. This is a measurement
  gate, not a product gate. Its FAIL branch terminates the trading-edge program.
  - Allowed work:
    - Fetch extended SUI/USDT 15m klines from Binance public API (read-only market
  data; target ≥18 months, minimum 12) into a research-only dataset — production DB
  untouched.
    - Apply the existing, unchanged triple-barrier contract to the extended window for
  labeling context.
    - Pre-register before any evaluation runs (in the scope-lock doc itself): (a) cost
  model — 0.10% taker fee per side, no BNB discount, plus fixed slippage allowance
  (e.g., 0.05% per side); (b) 4–6 deterministic signal families derived from existing
  features (e.g., EMA-cross trend follow, BB-breakout, momentum continuation, MACD
  regime) with fixed parameters; (c) controls: always-long, always-short, random-entry
  with identical exit logic.
    - Purged walk-forward expectancy evaluation: embargo ≥ 12 bars (the label horizon)
  at every fold boundary; report net expectancy in R and % per trade, overall and per
  regime segment.
    - One report artifact + result-decision doc + tests for the report logic.
  - Not allowed: ML model training; model promotion; runtime pointer updates;
  Telegram/dashboard dispatch; production/advisory behavior; threshold or parameter
  tuning after results are seen; adding signal families after results are seen;
  label/triple-barrier definition changes; DB mutation; Stage 2 revival.
  - Pass criteria: ≥1 pre-registered family with mean net expectancy > 0, 95% bootstrap
  CI above zero, and positive in at least 2 of 3 chronological regime segments —
  decided by the artifact, not by inspection.
  - Fail criteria: No family meets the pass bar.
  - Kill criteria: FAIL → recommended next gate =
  project_research_archive_closeout_result_decision; the trading-edge program stops,
  repo preserved as research artifact. Also kill if <12 months of clean data is
  obtainable (verdict BLOCKED → data-quality gate, not silent continuation) or if any
  post-hoc criteria modification is attempted.
  - Expected artifacts: artifacts/edge_existence_study_first_run.json,
  docs/cost-adjusted-edge-existence-study-result-decision.md,
  tests/test_edge_existence_study_report.py, plus the pre-registration block inside the
  scope-lock doc.

  What Not To Do

  - Don't write a close-out claiming "no edge exists" from the current evidence — it
  only supports "this design on this window failed."
  - Don't treat Stage 1's 0.93 PR-AUC as a salvageable asset; against an 0.866
  prevalence floor with boundary leakage, the real lift is marginal, and it predicts
  volatility, not direction.
  - Don't redesign Stage 2, retrain anything, or add features before edge existence is
  established on real history — that repeats the loop that just ended.
  - Don't touch costs, families, or thresholds after the study runs once. Single shot;
  artifact decides.
  - And per standing locks: no live trading, no promotion, no runtime pointers, no
  dispatch, no threshold tuning to force a pass.

✻ Baked for 5m 23s

※ recap: Strategic review of the SUI trading-signal project is done: Stage 1's
  strong-looking metrics are mostly a prevalence artifact and edge was never tested
  after costs. Next action: write the pending Stage 1 preservation result-decision doc,
  then the proposed cost-adjusted edge-existence study scope lock. (disable recaps in
  /config)
