# Jobs: the owner's neutral briefs and judges

Each job has one folder here that no competing agent edits:

- `README.md`: the brief (approved images, model files and their hashes, height, printer, owner decisions).
- `judge/judge.json` plus its files: the approved view(s) the referee compares against, the referee anchors (`@x,y,r` points per finish slot) and any masks. `"official": true` once the owner confirms it.

Agents do their work in `claude works/<job>/`, `codex works/<job>/` and so on, and submit with `submission.json`. The referee is `python scoreboard/score.py run <job>`. See [scoreboard/RULES.md](../scoreboard/RULES.md).

**To make a judge official**, the owner (or an agent on the owner's instruction) must:
1. Put in the exact image the 3D model was generated from, edited so every colour matches the final decisions (e.g. groom maroon, glass silver). Use a transparent PNG or a non-white background where white or ivory parts touch the edge.
2. Add back and side approved views if the customer has them, with `"yaw": 180` and so on.
3. Check every referee anchor on a gridded zoom. `approved_match.py` prints `CHECK ANCHOR` for suspicious ones.
4. Set `"official": true` and commit before the round starts.
