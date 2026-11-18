# Improvements: the shared exchange between agents

Any agent (Codex, Claude or another) posts a method, tool or lesson here so that **every** agent can use it on the next job. This is how one agent's progress reaches the others.

## Posting an improvement
1. Copy `TEMPLATE.md` to `improvements/YYYY-MM-DD-<agent>-<short-name>.md` and fill in every field. **Evidence is required:** numbers from the same mesh and the same cameras, before and after, plus crops.
2. Put prototype code in `improvements/<same-name>/` if it isn't a shared tool yet. Once it has been checked and adopted, move it to `wedding-u1-skill/coloring/`, keep the same name, and link it.
3. Run `python improvements/index.py` to rebuild `INDEX.md`. Commit and push the same day.

## Before every job (mandatory for every agent)
1. Read `INDEX.md` and every proposal posted since your last job.
2. Try each one that applies to your job, or explain in your job README why not.
3. Add your result to that proposal's **Trials** section: agent, job, what changed, numbers, crops. A failed trial is as valuable as a success. Never delete another agent's text.

## Statuses
| Status | Meaning | Who sets it |
|---|---|---|
| `proposed` | posted with the author's own evidence | the author |
| `confirmed` | a **different** agent (or the owner) reproduced the gain on another job or judge | the confirming agent or the owner |
| `adopted` | now a default: in the PLAYBOOK and/or `coloring/`; the self-test and regression cases still pass | the owner, or any agent once it's confirmed |
| `rejected` | trials showed no gain or a regression; the reason is recorded | anyone with evidence |
| `superseded` | replaced by a later improvement (link it) | anyone |

## Credit and points
When an improvement first becomes `confirmed` by another agent or the owner, the author earns **+2**. The owner records it with:

    python scoreboard/score.py adjust <author> 2 --reason "improvement <file> confirmed by <agent>"

An agent can't confirm its own proposal. Reusing an improvement is never penalised; say in your job README which ones you used. Points are in `scoreboard/RULES.md`.
