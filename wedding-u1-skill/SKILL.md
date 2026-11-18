---
name: wedding-figurine-u1
description: Reproduce the 150 mm Snapmaker U1 wedding figurine, its seven-color hand-painting guide, two-swap print mapping, flat multiview checks and finished hero render. Adapt the workflow to another sculpt by retracing its regions.
---

Read AGENT-PROMPT.md for the job specification and stage map. For the supplied couple, execute the bundled replay in an empty job directory. The expected folder contains the delivered models and hero for direct handoff or comparison. Use scripts/verify.py after replay. Use history only to inspect earlier experiments. The final recipe supersedes those experiments.

For installation, extract the entire wedding-u1-skill folder. A skill-discovering agent can place it under ~/.agents/skills/ or ~/.claude/skills/. The commands also work when run directly from the extracted directory.
