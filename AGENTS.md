# Instructions for every agent in this repo (Codex, GPT, Claude and others)

This repo turns customer-approved images and generated 3D models (Tripo, Meshy) into multicolour figurine print files for the owner's Snapmaker U1.

**Read and follow [FIGURINE-AGENT-PROMPT.md](FIGURINE-AGENT-PROMPT.md) for every colouring job.** In short:

1. The approved image is the colour truth. Match it 1:1 with no leaks or patches.
2. Nothing is delivered until `wedding-u1-skill/coloring/approved_match.py` reports PASS on the exported finish guide for every approved view, and you have reviewed every tile and patch crop yourself.
3. Read `wedding-u1-skill/PLAYBOOK.md` and the latest `wedding-u1-skill/LEARNING-LOG.md` entries first. Add to both after every job or review round, turn every owner-found defect into a regression case, and push the same day.
4. Work in your own branch and job folder (`jobs/<model>/` or your agent folder such as `gpt works/`). Merge findings from other agents into the playbook, and note the source.

`CLAUDE.md` holds the same rules for Claude Code sessions.
