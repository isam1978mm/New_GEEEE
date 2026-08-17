# AUDIT READ FIRST - Private Local App Context

## Required audit context

This repository is being treated as a **private/local operator app**, not a public-release product and not a public-sharing package.

Future audits must read this file before judging the app, planning changes, or recommending cleanup.

## Canonical local runtime

The main local FastAPI app uses:

```text
host = 127.0.0.1
port = 8007
base URL = http://127.0.0.1:8007
```

Future sessions must use port **8007** for normal app/API/health/readiness commands unless the operator explicitly changes it. Do **not** infer port 8000 from Uvicorn defaults. Purpose-specific test harnesses may use their own separately documented ports without changing the main app port.

## Main rule

Do **not** make public-safe redaction, public exposure hardening, neutralized wording, artifact hiding, or coordinate suppression the default audit priority.

The current priority is:

```text
private/local output correctness
operator usefulness
notebook/app parity where appropriate
clear provenance
clear uncertainty
data-quality blocking
reliable artifact generation
no misleading successful outputs
```

## What future audits should not do by default

```text
Do not remove useful private/local outputs only because they are not public-safe.
Do not hide local operator artifacts only because they contain detailed diagnostics.
Do not convert rich local results into public-neutral summaries unless explicitly requested.
Do not treat browser/public-sharing safety as the main product goal.
Do not assume this app is intended to be published or shared publicly.
Do not reopen old public-safe cleanup work unless the operator explicitly asks for a public-release track.
```

## What still must remain protected

Private/local does **not** mean careless.

Do not commit or paste into public docs, Git, issues, or chat:

```text
real exact coordinates
private target geometry
raw KMZ/KML/GeoJSON bodies from real runs
raw raster arrays or NPY contents
private run folders or sensitive local absolute paths
service-account material or credentials
private hashes tied to sensitive local artifacts
real protected-location site lists or labels
```

## Correct audit posture

Future audit should classify findings like this:

```text
Reliability bug: fix.
Notebook parity gap: document or port.
Private/local operator output: keep if useful.
Public-safe concern only: ignore unless a public-release track is explicitly opened.
Misleading certainty: fix wording.
Physical-world confirmation claim: do not make it.
```

## Current project interpretation

This app may produce local/private geospatial and diagnostic artifacts for the operator.

Those artifacts are allowed to be rich and detailed inside the private local runtime.

The app should still avoid unsupported certainty. Satellite/software outputs are signal analysis outputs, not physical confirmation.

## Read order for future sessions

1. Read this file first.
2. Read `AGENTS.md`, including the canonical local runtime rule (`127.0.0.1:8007`).
3. Inspect current git status and recent commits.
4. Inspect the relevant code/docs for the requested task.
5. Do not start by applying public-safe assumptions from older documents.
6. Keep real private samples and sensitive run contents out of Git and chat.
