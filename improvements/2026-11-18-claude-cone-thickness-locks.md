---
title: Part locks by cone thickness — thin networks (glasses, wire jewellery) and thin-part-vs-body contacts
author: claude
date: 2026-11-18
status: confirmed
applies_to: glasses frames, wire jewellery, straps, hands on clothes, arms on torso, ears in hair
tool: wedding-u1-skill/coloring/thin_network_lock.py, wedding-u1-skill/coloring/part_lock.py
---

## Problem
Colour masks fail where two materials touch, because the texture is blurred and shaded at contacts. Glasses kept skin patches through two review rounds, and a thumb on a trouser leg had a ragged edge.

## Method
- **Thickness:** fire 9 inward rays per face (the axis plus 8 at 40°) and keep the shortest exit. A half-buried wire still exits quickly in some direction.
- **Thin networks:** faces thinner than about 1.5× the wire diameter, kept as connected networks of ≥ 300 faces, are painted one colour as the very last step.
- **Contacts:** in a band around the boundary, thin faces belong to the part and thick faces to the body. Then a binary min-cut with a strong crease prior.

## Evidence (author, man-with-drink, PLAYBOOK §4.1)
- Glasses: 29,673-face frame network at 1.25 mm. **The owner confirmed "Glasses done"** (round 3).
- Thumb: thin 7 mm, thick 10 mm, 10 rings, λ 3; 914 faces changed. Clean at 45 px/mm, and the owner moved on (round 4).

## How to use it
Use after broad labels and crease snap, and **apply the locks last**, before the contour split. Parameters are in `coloring/README.md`.

## Trials (other agents append here; never edit someone else's entry)
| Date | Agent | Job | Result (numbers) | Verdict |
|---|---|---|---|---|
| 2026-11-18 | owner | man-with-drink | Glasses accepted round 3; hand accepted round 4 | confirmed by the owner (before the points system existed; no points awarded retroactively unless the owner chooses) |
