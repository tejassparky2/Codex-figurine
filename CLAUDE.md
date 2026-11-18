# Instructions for agents working in this repo

This repo turns textured 3D models and photos into multicolour figurine print files for the owner's Snapmaker U1. The owner wants the colouring method to **improve with every model and be saved to GitHub every time**.

## Before colouring anything

0. Follow the mission prompt in `FIGURINE-AGENT-PROMPT.md` (shared with all agents through `AGENTS.md`). The core rule: nothing is delivered until `wedding-u1-skill/coloring/approved_match.py` reports PASS against every customer-approved view and you have reviewed every tile and patch crop yourself.
1. Read `wedding-u1-skill/PLAYBOOK.md`: standing preferences, filament stock, the default pipeline, proven techniques and failures.
2. Skim the latest entries in `wedding-u1-skill/LEARNING-LOG.md`.
3. Use the generic tools in `wedding-u1-skill/coloring/`. Copy model-specific steps from the most similar job in `claude works/` (or learn from `codex works/`, without editing it).

## Standing preferences (details in the playbook)

- Send **straight-front previews** (full figure and face), rendered from the exported file, with **every** revision.
- Realistic models: no catchlight dot and no eyeliner wing. **Never black inside a mouth.**
- Glasses and other thin parts are locked to one colour by geometry, applied as the last step.
- No colour leaks at contacts: hands, hems, collars, hairlines.
- Use only filaments from the stock list. Say plainly what was substituted.

## Learning protocol: after every review round and every delivery

1. Add a dated entry to `wedding-u1-skill/LEARNING-LOG.md`: **what** the owner flagged, **how** it was fixed (tool and parameters), **why** it failed and why the fix works, **when** to reuse it, and the **result**.
2. Update `wedding-u1-skill/PLAYBOOK.md` if best practice changed. That covers preferences, defaults, techniques, failures and the model log.
3. Make a fix generic: move it into `wedding-u1-skill/coloring/` once it works without model-specific coordinates, and test it on the job that produced it.
4. Work only in `claude works/<job>/` (the neutral brief and judge are in `jobs/<job>/`; see `scoreboard/RULES.md`). Keep the job complete there: scripts as run, `run_all.sh`, inputs, the verified 3MFs, previews and the record.
5. **Commit and push the same day** to the session's working branch. Never commit `__pycache__`, virtual environments or scratch arrays.
6. Every defect the owner finds becomes a regression case under `claude works/<job>/regression/`, and the approval gate must FAIL the defective version.
7. **Exchange improvements through `improvements/`** (see its README). Before every job, read `improvements/INDEX.md` and add trials to the proposals you test. After a gain, post a proposal with gate evidence and run `python improvements/index.py`.
8. When another agent shares findings, merge them into the playbook, note the source, and record any conflicts with how they were resolved.

Be precise about verification. A decoded paint array, a rendered preview, a slicer preview, the G-code and a physical print are five different checks. Record which ones were actually done.
