# Competition rules

Every agent (Claude, Codex and any other) works in its own folder and is scored by the same referee. The owner's verdict counts most, because the customer is the real judge.

## Folders: who owns what
| Folder | Owner | Contents |
|---|---|---|
| `claude works/<job>/` | Claude agents only | tools as run, outputs, `submission.json`, review notes |
| `codex works/<job>/` | Codex/GPT agents only | the same |
| `<name> works/` | any new agent | create it on your first job; the referee finds it automatically |
| `jobs/<job>/` | the owner (neutral) | the brief, input hashes and the **judge**: approved images, referee anchors, masks |
| `wedding-u1-skill/coloring/`, `scripts/`, `PLAYBOOK.md`, `LEARNING-LOG.md` | shared | tools and knowledge every agent uses; contributions are credited in the log |
| `scoreboard/` | the referee | `score.py`, `ledger.json` (append-only), `SCOREBOARD.md` (generated) |

Never edit another agent's folder or the judge of a job you are competing in. You may read and learn from everything. If you reuse another agent's method, say so in your README and the log.

## Submitting
Put `submission.json` in `<agent> works/<job>/`:
```json
{"finish_guide": "out/<model>-finish-guide.3mf", "printer_project": "out/<model>-U1.3mf", "round": 1, "notes": "what changed"}
```
The finish guide must be a single painted mesh with solid per-face codes, the same format the gate reads.

## How the referee scores a round
`python scoreboard/score.py run <job>` runs `approved_match.py` on every submission, using the job's judge views, referee anchors and masks. The judge's hash is stored with each result.

| Event | Points |
|---|---:|
| Gate PASS on every judge view | +3 |
| Best submission of the round (head-to-head) | +2 |
| Head-to-head tie (clear disagreement within 5 % of each other, or 0.02 points) | +1 each |
| Submission missing a file, unreadable, or not a single painted mesh | −1 |
| **Owner accepts the delivery** (`score.py owner <job> <agent> accept`) | **+5** |
| Accepted in the first review round (`--first-round`) | +2 |
| Owner finds a defect the agent did not report (`score.py owner <job> <agent> defect --note …`) | −1 each |
| Adjustment by the owner (`score.py adjust`), e.g. a shared tool adopted after an A/B (+2) or a commit that broke the gate self-test (−3) | as stated |

**Ranking in a head-to-head:**
1. Verdict tier: PASS, then NEEDS_REVIEW, then FAIL. CANNOT_JUDGE and INVALID are not ranked.
2. Then the lower clear-disagreement %.
3. Then the smaller largest clear-error patch.

**Practice rounds** are recorded with `would_be_points` but score 0. A round is practice when the judge isn't marked `"official": true`, or when run with `--practice`. A judge is made official once the owner confirms its approved images and anchors.

## Fair play
- **The judge is fixed before the round.** Agents may *propose* judge anchors or masks in their own folder, but only the owner promotes them into `jobs/<job>/judge/`.
- **Don't tune against the judge's hidden failure modes.** Fix the model, not the measurement. If you think the gate is wrong, show it with crops and propose the change to the shared tool. It's adopted only if the gate self-test still passes.
- **Honest reporting counts.** A defect you report yourself costs nothing; one the owner has to find costs a point.
- **Hidden sides aren't measured by the gate.** The owner's verdict covers them.
