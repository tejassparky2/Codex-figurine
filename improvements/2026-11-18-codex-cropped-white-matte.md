---
title: Recover the silhouette of a cropped figurine on white
author: codex
date: 2026-11-18
status: proposed
applies_to: inspection of partial RGB reference views with known white background
tool: codex works/experiments/2026-11-18-corner-matte/white_margin.py
---

## Problem

A clean figurine cropped through its upper-left corner scored CANNOT_JUDGE. The reference matte filled the entire frame. The comparison image marked the empty background blue.

## Method

Pad the RGB reference with ten white pixels on each side. Apply the existing gate foreground routine, remove the padding, and supply the result as an explicit mask. This gives the border-color estimator known white samples and the flood fill an exterior seed with a path around the frame. Keep the approved RGB image and the camera in their original coordinates.

## Evidence (author)

On the known clean crop, silhouette IoU increased from 0.5244 to 0.9910. Disagreement stayed at 0%, largest clear error at 0 mm², review patches at zero, and boundary p95 at 0.156 mm. The verdict became PASS. On the full front practice portrait IoU moved from 0.9516 to 0.9513 and the verdict stayed FAIL. The original self-tests passed at 30 and 1,500 faces. With the new masks and solved cameras the same four control verdicts and top patch records were reproduced. Flat and reviewed replays matched their checkpoints.

[Commands, before/after crops and complete metrics](../codex%20works/experiments/2026-11-18-corner-matte/README.md)

## How to use it

From repo root, run the command below, inspect the silhouette, and pass the PNG to the gate with `--mask`. Use it on **known white RGB** partial views where the foreground touches the upper-left corner. Prefer source alpha when available. Neither padding nor color distance can recover an unmarked white-on-white boundary.

```sh
python "codex works/experiments/2026-11-18-corner-matte/white_margin.py" approved.png foreground.png
```

## Trials (other agents append here; never edit someone else's entry)
| Date | Agent | Job | Result (numbers) | Verdict |
|---|---|---|---|---|
