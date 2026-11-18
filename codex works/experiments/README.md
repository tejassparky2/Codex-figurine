# Wedding figurine research sprint

The registered finish guide still fails the front practice judge at 0.6953% disagreement. This sprint adds an attribution check for the leak audit and a mask helper for a specific partial-view failure. It does not release a recolored wedding mesh.

| Experiment | Primary result | Recommendation |
|---|---|---|
| [Audit overlap](2026-11-18-audit-overlap/) | 0.8594 → 0.9316% with adaptive registration. Zero edited triangles in either patch list. | Adopt face-ID attribution when a paint revision worsens the gate. Retain unresolved audit suggestions for review. |
| [Cropped white background](2026-11-18-corner-matte/) | Clean partial-view IoU 0.5244 → 0.9910. Both planted defects still detected. | Use the mask helper when the top-left seed lands on the model against known white. |
| [Shadow weighting](2026-11-18-shadow-weight/) | Practice disagreement 0.8594 → 0.8865%, boundary p95 0.688 → 0.715 mm. | Retain the existing coefficient. |

[What was already known](KNOWLEDGE.md) · [Environment, replays and scoreboard baseline](ENVIRONMENT.md)

### Next three trials

1. Freeze the reference warp across paired exports and plant defects at material edges adjoining hands and garlands. Check that the measured change lands on the edited triangle IDs.
2. Decode the owner's saved Orca brush subdivisions as ground truth. Hold out entire contact regions and a second figurine to test the leak proposals before applying them.
3. Obtain matching approved side and back views or source alpha, then measure the plume, strand of white flowers, cuffs and occluded hands in each view. Publish coverage and uncertain regions alongside the score.
