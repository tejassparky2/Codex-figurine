# GPT works

GPT experiments and deliverables live here. Other agents can keep their own branches and model folders. This record carries verified results from one figurine to the next.

## Wedding couple, round 2

The starting inputs were the published leak-audit candidates. The eight contact regions were traced again on front and back renders of the original UV texture. The new pass fixes confident interior seeds, solves a weighted graph on visible neighboring faces in a narrow band, and permits only the material substitutions specified for each region. This targets the hands against the garland, the coat at the cuff and the reverse side of the hanging flowers. The source texture and approved finish palette serve different roles. The requested black-and-white eyes and solid-gold jewelry take precedence over photographic highlights.

Next, the other agent's contour splitter cuts across triangles instead of following their staircase edges. We ported it from their man-with-drink experiment, with its protected-region behavior and a connected-components implementation of the keep-mask propagation. The bed contact, upper face details and two upright spool-change boundaries are protected in this experiment. The method retains the same surface and transfers physical tool assignments by the parent face and the scheduled pigment. A smooth contour can still surround a patch of the wrong material.

[Finish guide](Wedding-contours-guide.3mf) · [Upright four-head project](Wedding-contours-U1.3mf) · [Matched close-ups](wedding-ab.png) · [Experiment results](results.md) · [Research and evidence](research.md) · [Uploaded tilted G-code analysis](tilted-print.md)

### Replay

Start with the repository's reviewed replay and leak audit. Use their pinned Python environment. Set JOB to the reviewed replay output, AUDIT to the audit output and REPO to the repository root. Run these commands from this directory.

    python wedding_contacts.py "$JOB" "$AUDIT/finish.npy" contacts.npy
    python run_wedding.py "$JOB/repaired-u1.npz" contacts.npy "$REPO/Wedding-leak-candidate-U1.3mf" "$REPO/Wedding-leak-candidate-guide.3mf" out --base-labels "$AUDIT/finish.npy"
    python compare.py out/scaled.npz "$AUDIT/finish.npy" out/contours.npz comparison.png

The upright U1 project inherits the candidate's four 0.2 mm nozzle preset. The separately uploaded tilted G-code uses a different profile, orientation and manually edited paint. The new project needs its own setup and slice. Work from the user's saved edited project when their brush strokes are available.

### How to carry results to the next model

1. Record the source hash, intended material per part, nozzle profile, reference views and the user's actual correction file. Keep the manually edited file as the approval reference.
2. Record each reproduced failure as an annotated view or labeled face region. Include the back, underside and protected details next to each repair. For split geometry, retain parent IDs and evaluate the sampled physical surface; a raw face-index comparison becomes invalid after subdivision.
3. Compare the existing pipeline, the other agent's method alone, and the combined candidate on the same mesh and cameras. Log what changed at each stage. Evaluate disputed contacts separately from thin details such as eyelashes.
4. Count incorrect area inside independently approved masks, movement of correct boundaries, altered protected features and mesh defects. Compare the actual sliced exterior paths at the chosen nozzle and orientation. A reduced boundary length or fewer islands alone cannot demonstrate better semantic accuracy.
5. Promote a technique only for the defects and models it improved. Record regressions and retain the preceding files. On a new sculpt, reuse the algorithm and evaluation procedure; re-establish camera registration, finish labels, seeds, protected features and spool schedule.
