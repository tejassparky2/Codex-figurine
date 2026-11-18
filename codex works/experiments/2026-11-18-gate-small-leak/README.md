# 2026-11-18 · Approval-gate small-leak threshold

**Hypothesis.** The gate can pass a real planted leak below the 0.6 mm² largest-patch threshold.

**Method.** Ran `approved_match_selftest.py` unchanged, varying `--patch-faces` from 1 to 1,500. The 10-face case is a visible face patch of 2.2 mm² of surface. It is below the former 0.6 mm² projected-patch threshold. The gate change lowers the default largest-patch threshold from 0.6 to 0.10 mm² while retaining the 30- and 1,500-face regressions.

**Before**

| Patch | Surface area | Gate largest patch | Verdict |
|---|---:|---:|---|
| 1 face | 0.3 mm² | none | PASS |
| 10 faces | 2.2 mm² | 0.171 mm² | PASS |
| 30 faces | 6.8 mm² | 3.296 mm² | FAIL |
| 1,500 faces | 147.5 mm² | 102.165 mm² | FAIL |

**After threshold 0.10 mm²**

| Patch | Surface area | Gate largest patch | Verdict |
|---|---:|---:|---|
| 1 face | 0.3 mm² | none | PASS (kept as a below-print-feature limitation) |
| 10 faces | 2.2 mm² | 0.171 mm² | FAIL |
| 30 faces | 6.8 mm² | 3.296 mm² | FAIL |
| 1,500 faces | 147.5 mm² | 102.165 mm² | FAIL |

**Vision.** The 10-face crop is a small but visible local wrong slot, not a 0.171 mm² category change at the silhouette boundary.

**Verdict.** Adopt threshold change after rerunning the 1-, 10-, 30-, and 1,500-face self-tests and the earlier replay. A 1-face leak may remain below the smallest physically meaningful print feature and is reported as expected limitation, not a pass for a 10-face leak.
