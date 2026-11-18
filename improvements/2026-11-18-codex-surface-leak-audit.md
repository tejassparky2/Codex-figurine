---
title: Surface leak audit — two-scale texture/normal neighbour vote with connected-path rule
author: codex
date: 2026-11-18
status: proposed
applies_to: paint spill across sculpted edges, saved Orca brush corrections
tool: wedding-u1-skill/reviewed/leak_audit.py, wedding-u1-skill/reviewed/export_leak_candidate.py, wedding-u1-skill/scripts/compare_orca_paint.py
---

## Problem
Paint spills across sculpted edges were found only by eye. Manual Orca re-saves also changed paint silently.

## Method
Each face gets a k-nearest-neighbour vote from confident interior faces, using position, Lab texture colour and normals, at radii 1.3 and 3.2 mm.
- A change is applied only if both scales agree, confidence is ≥ 0.94, and an edge-connected path reaches existing paint of the proposed colour.
- Protected masks and approved labels override the vote.
- `compare_orca_paint.py` compares a candidate with the owner's saved Orca project, including split brush paint.

## Evidence (author; see `wedding-u1-skill/reviewed/LEAK-CHECK.md`)
- 812,934 faces scanned; 7,899 flagged; 1,669 changed; 6,230 held for review.
- Replayed byte-for-byte by Claude. `compare_orca_paint.py` agrees: exactly 1,669 encoded differences.

## How to use it
Run it after the reviewed paint, with a protect mask for faces and soles. Inspect the held findings; don't apply them blindly.

## Trials (other agents append here; never edit someone else's entry)
| Date | Agent | Job | Result (numbers) | Verdict |
|---|---|---|---|---|
| 2026-11-18 | claude | wedding-couple (practice judge, front view only) | Clear disagreement 0.859 → 0.932 %, largest clear error 16.2 → 22.9 mm² against the reviewed release | **Slight regression on the visible front.** The changes may help hidden surfaces the judge can't see, or the vote may follow texture where the approved art differs. Next: run the gate's patch list on the 1,669 changed faces to separate the two |
| 2026-11-18 | codex | wedding, fixed-camera face-ID intersection | 168/1,669 changed faces visible, zero in either patch list. All 1,128 newly hard and 782 resolved pixels lay on other triangles. Locked-camera rigid control 3.7540 → 3.7540%. | Use as proposals for review. Front score regression is sensitive to refitting the reference warp. Rear correctness remains unknown. |
