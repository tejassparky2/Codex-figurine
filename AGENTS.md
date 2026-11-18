# Instructions for every agent in this repo (Codex, GPT, Claude and others)

This repo turns customer-approved images and generated 3D models (Tripo, Meshy) into multicolour figurine print files for the owner's Snapmaker U1.

**Read and follow [FIGURINE-AGENT-PROMPT.md](FIGURINE-AGENT-PROMPT.md) for every colouring job.** In short:

1. The approved image is the colour truth. Match it 1:1 with no leaks or patches.
2. Nothing is delivered until `wedding-u1-skill/coloring/approved_match.py` reports PASS on the exported finish guide for every approved view, and you have reviewed every tile and patch crop yourself.
3. Read `wedding-u1-skill/PLAYBOOK.md` and the latest `wedding-u1-skill/LEARNING-LOG.md` entries first. Add to both after every job or review round, turn every owner-found defect into a regression case, and push the same day.
4. **Work only in your own agent folder**: `codex works/<job>/` for Codex/GPT, `claude works/<job>/` for Claude, `<name> works/<job>/` for any other agent. `jobs/<job>/` holds the owner's neutral brief and judge, and shared tools live in `wedding-u1-skill/`. Never edit another agent's folder or the judge.
5. **The agents compete.** `scoreboard/score.py run <job>` scores every agent's `submission.json` with the same approval gate and judge. The owner's acceptance is worth the most. Rules and points are in [scoreboard/RULES.md](scoreboard/RULES.md); standings are in [scoreboard/SCOREBOARD.md](scoreboard/SCOREBOARD.md).
6. **Share improvements in [`improvements/`](improvements/README.md).**
   - Before every job, read `improvements/INDEX.md` and every new proposal. Try the ones that apply, and add your result to that proposal's Trials table.
   - When you find something better, post it there with before/after numbers from the gate, so every agent gets it.
   - The author earns +2 when a *different* agent or the owner confirms it. Learning from a rival is encouraged; say what you reused.

`CLAUDE.md` holds the same rules for Claude Code sessions.
