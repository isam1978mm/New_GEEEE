# Reference Run Fixture Notes

This directory documents the notebook reference run used for parity capture.

## Purpose

- Record how the reference notebook outputs were produced.
- Preserve enough context to regenerate fixture-derived expectations.
- Avoid storing sensitive or oversized binary payloads by default.

## Minimum Capture Notes

- Notebook file and revision used
- Capture date
- Reference ROI statement confirming it is deliberately uninteresting
- Which stage outputs were inspected or retained
- Any normalization or scrubbing applied before commit
- Any parity exception that affected interpretation

## Binary Fixture Policy

- Prefer derived text notes, small arrays, or synthetic fixtures.
- Do not commit huge binaries for M13.
- If a future milestone requires committed binary references, add an ADR-backed note explaining why.
