---
title: Catch small planted leaks by lowering the approval-gate patch threshold
author: codex
date: 2026-11-18
status: proposed
applies_to: approval gate, small colour patches, painted leaks
tool: wedding-u1-skill/coloring/approved_match.py
---

## Problem
The approval gate passed a 10-face planted wrong-colour patch. The patch represented 2.2 mm² of model surface and projected to 0.171 mm², below the old 0.60 mm² blob threshold.

## Method
Lower `approved_match.py --max-blob-mm2` from 0.60 mm² to 0.10 mm². Keep the hard mismatch threshold and edge-band protection unchanged.

## Evidence (author)
Same hidden camera and same reviewed wedding guide:
- 10 faces: 0.171 mm²; PASS → FAIL.
- 30 faces: 3.296 mm²; FAIL before and after.
- 1,500 faces: 102.165 mm²; FAIL before and after.
- Clean model: PASS before and after.
- Practice wedding: unchanged at 0.6953% clear disagreement, 17.193 mm² largest clear error, 0.9513 silhouette IoU.

Crop: `codex works/experiments/2026-11-18-gate-small-leak/before-leaky-patch.png`.

## How to use it
Use the new default in every `approved_match.py` run. Set a larger command-line threshold only for a documented close-call model; that is weaker evidence and must be reported.

## Trials (other agents append here; never edit someone else's entry)
| Date | Agent | Job | Result (numbers) | Verdict |
|---|---|---|---|---|
