---
name: wedding-figurine-u1
description: Prepare and inspect multicolor figurines from textured meshes and reference photographs, map finished colors to printer tools, and reproduce the reviewed 150 mm wedding example. Read PLAYBOOK.md first; it accumulates what worked on every model.
---

**Before colouring any model, read [the colouring playbook](PLAYBOOK.md)**. It lists the owner's standing preferences, the filament stock, the default pipeline, the techniques that worked and the failures to avoid. After every review round, add a dated entry to [LEARNING-LOG.md](LEARNING-LOG.md) (what, how, why, when, result), update the playbook, and push. The generic tools are in [coloring/](coloring/README.md).

For a **new model**, follow [the A–Z agent prompt](NEW-MODEL-PROMPT.md). Use the toolkit CLI for initial labeling and the layer-color script for scheduling. Trace the new sculpt from its own references and record its camera, regions and printer settings.

For **the wedding model**, follow the [original stages](AGENT-PROMPT.md) for source-to-flat and the [reviewed stages](reviewed/README.md) for repair, final paint and inspection. Preserve the repository structure for replay. To register this skill locally, link the wedding-u1-skill directory from the full clone into your agent's skills directory.
