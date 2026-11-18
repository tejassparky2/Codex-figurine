# Wedding comparison and decision

| Variant | Triangles | Total finish-color interface length |
|---|---:|---:|
| Prior texture leak candidate | 812,934 | 6,847.6 mm |
| Prior candidate plus the other agent's contour strategy | 833,010 | 6,718.2 mm |
| Revised contact seeds, before splitting | 812,934 | 6,938.7 mm |
| Revised contacts plus protected contour split | 832,906 | 6,809.6 mm |

A texture-only pass had left ivory across the bride's hand and skin on the groom's cuff. Contour smoothing alone retained those broad errors. The source-guided contact pass reassigned 2,305 original faces. Splitting the revised contacts shortened their boundaries by 129.1 mm and changed the material on 45.4 mm² of surface. Interface length measures geometric complexity, not semantic accuracy. The seed pass restored material boundaries and thus increased total length before smoothing.

The exports were reopened and the decoded paint labels matched the intended arrays. Snapmaker Orca reported one manifold body and 150 mm height. The splitter checked edge incidence, winding, body count, area preservation and protected faces. The new keep-mask implementation matched the upstream output on a seeded synthetic sphere. CLI model inspection also emitted a plate-exclusion diagnostic; the result above concerns model geometry. No new final G-code or physical print was verified.

The matched close-ups show a clearer silhouette where the bride's hand meets the garland. The oblique view still shows a skin-colored area on the ivory strand under the cuff and a ragged contact at its edge. This release is a candidate. Use the saved manually corrected wedding project to establish acceptance. Next useful evidence is the same pose viewed from underneath with an approved face mask or the saved brush strokes. An unsupervised pass over every similarly colored bead could erase intended skin on the adjacent hand.
