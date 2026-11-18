# Codex figurine

**Agents: start with the [mission prompt](FIGURINE-AGENT-PROMPT.md).** Nothing ships until the [approval gate](wedding-u1-skill/coloring/approved_match.py) passes against the customer-approved image and the tile review is done.

**Each agent works in its own folder:** [`claude works/`](claude%20works), [`codex works/`](codex%20works), and so on. The owner's neutral job briefs and judges are in [`jobs/`](jobs). A referee scores every agent with the same gate: [rules](scoreboard/RULES.md) · [scoreboard](scoreboard/SCOREBOARD.md).

**For another figurine, give your agent the [A–Z agent prompt](wedding-u1-skill/NEW-MODEL-PROMPT.md).** It covers source alignment, paint-region cleanup, geometry repair, layer-color conflicts, spool swaps, multiview inspection and slicer verification. The [installable skill](wedding-u1-skill/SKILL.md) points agents to the toolkit and the worked example.

**Colouring playbook:** [wedding-u1-skill/PLAYBOOK.md](wedding-u1-skill/PLAYBOOK.md) collects what worked and failed on every model. The generic tools are in [wedding-u1-skill/coloring/](wedding-u1-skill/coloring/README.md).

## Man with drink (220 mm caricature)

[U1 print project](claude%20works/man-with-drink/out/Man-with-drink-U1-220mm.3mf) · [Finish guide](claude%20works/man-with-drink/out/Man-with-drink-220mm-finish-guide.3mf) · [Front preview](claude%20works/man-with-drink/out/Man-with-drink-front.png) · [Job record](claude%20works/man-with-drink/README.md)

Four heads: Apricot, Black, Simply Silver and Orange. At 120 mm, pause and swap Orange for Pure White. The glasses frames are locked silver by geometry. Not yet sliced or printed.

## Reviewed wedding couple

[150 mm U1 print project](Wedding-U1-150mm-reviewed.3mf) · [Finished-color guide](Wedding-150mm-reviewed-paint-guide.3mf) · [23-page color inspection](Wedding-color-inspection.pdf)

The [reviewed replay](wedding-u1-skill/reviewed/README.md) documents the final files, scripts and remaining print checks. The earlier [flat-stage replay](wedding-u1-skill/AGENT-PROMPT.md) covers registration, graph-cut segmentation, face tracing, smoothing and the hero render. Its [verification record](wedding-u1-skill/VERIFICATION.txt) applies to the flat release.

Clone or download the full repository to use the reviewed replay, which reads both bundled inputs and root-level 3MF checkpoints.
