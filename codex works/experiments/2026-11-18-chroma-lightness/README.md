# 2026-11-18 · Chroma-heavy approved-art labelling

**Hypothesis.** Down-weighting Lab L* makes shadowed cream and face skin easier to separate without self-calibrating to lightness.

**Method.** Copied `approved_match.py` and changed the Lab prototype weight from `[0.45, 1, 1]` to `[0.10, 1, 1]`. Ran the same wedding 25-anchor front judge and the clean/30/1,500-face self-test pattern on the experimental copy.

**Numbers**

| Result | Clear disagreement | Largest clear error mm² | Patches | Review patches | Boundary p95 mm | Silhouette IoU |
|---|---:|---:|---:|---:|---:|---:|
| Baseline weight 0.45 | 0.6953% | 17.193 | 41 | 3 | 0.604 | 0.9513 |
| Chroma-heavy weight 0.10 | 1.5802% | 61.510 | 53 | 3 | 0.688 | 0.9513 |

**Vision.** The largest patch moves to a maroon/black region and the global mismatch worsens. The 25-anchor run adds one more bad anchor warning.

**Verdict.** Reject this weight as a default. The experiment regressed both disagreement and largest error; it does not improve the sampled shadow problem.
