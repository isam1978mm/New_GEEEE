# V6-REAL-SCORING-1 Candidate Scoring And Ranking

## Current Status

V6-REAL-SCORING-1 adds a pure app-side scoring service over reduced feature rows.

Implemented now:

- scoring thresholds;
- candidate score formula;
- remote-sensing contrast formula;
- S2 confidence formula;
- v5-style warning flags;
- v6 building warning flag;
- v6 road-like warning flag;
- v6 false-positive warning count;
- v6 false-positive penalty;
- v6 quality-adjusted score;
- v6 no-warning bonus;
- v6 review priority score;
- deterministic final candidate ranking;
- safe candidate summaries;
- unit tests.

This is still not the full real V6 output path. The scoring service expects reduced feature rows. The next missing bridge is reducing the feature stack over grid cells and feeding those rows into this scorer.

## Added Files

```text
app/services/v6_real_scoring.py
tests/unit/test_v6_real_scoring.py
```

## What The Scorer Does

The scorer accepts per-grid-cell feature rows and produces ranked `V6ScoredCandidate` records.

It does not call the external geospatial service.

It does not read package files.

It does not create request zones yet.

## Ranking Logic

Candidates are sorted by:

1. lower v6 false-positive warning count;
2. higher top-10 stability count;
3. higher seasonal top-10 stability count;
4. higher top-25 stability count;
5. higher seasonal top-25 stability count;
6. higher v6 review priority score;
7. cell ID as deterministic tie-breaker.

## Safety Rules

- Scoring is pure Python.
- Unit tests are offline.
- Safe summaries do not include feature values or geometry bodies.
- Package writing stays separate.
- Request-zone creation stays separate.
- UI/API exposure is not added in this step.

## Still Not Done

- reduce feature stack to grid-cell rows;
- request-zone generation;
- feed scored candidates into the package writer;
- private app generate/review/download flow.

## Next Step

```text
V6-REAL-REDUCE-1: reduce the feature stack to per-grid-cell rows and connect those rows to the V6 scorer.
```

## Checklist

- [x] Add scoring thresholds.
- [x] Add candidate score formula.
- [x] Add remote-sensing contrast formula.
- [x] Add warning flags.
- [x] Add v6 false-positive warning count.
- [x] Add v6 false-positive penalty.
- [x] Add v6 quality-adjusted score.
- [x] Add v6 review priority score.
- [x] Add deterministic final ranking.
- [x] Add safe summaries.
- [x] Add unit tests.
- [ ] Reduce feature stack to grid-cell rows.
- [ ] Generate request zones.
- [ ] Feed real outputs into package writer.
- [ ] Add private app generate/review/download flow.
