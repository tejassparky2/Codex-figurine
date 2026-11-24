# AI research lab (v1)

Owner-operated coordinator for Claude, Codex and Gemini. Existing scoreboard and improvements exchange remain unchanged. No automatic provider calls, merging, or pushing. The judge adapter is not yet implemented for the figurine stress suite.

## Run a round (Windows PowerShell, Python 3.10+)

From a clean checkout of the lab branch:

    git fetch origin
    git switch ai-lab/orchestrator-v1
    python ai_lab/tournament.py start ../figurine-round-01 --round gate-01 --base HEAD --task-file ai_lab/first-task.md

Use three separate agent sessions, one per generated worktree, and paste the matching task markdown from the round directory. Each agent must commit its changes. Do not share customer images with a provider without authorization.

    python ai_lab/tournament.py freeze ../figurine-round-01

Give each agent its generated review markdown. Reviews are advisory: no agent votes determine the winner. Candidate SHAs remain fixed. Save review reports outside the worktrees.

## Independent judge

Copy judge.example.json to a separate owner-controlled directory outside the repository and round. Replace the placeholder executable and script with your trusted local benchmark adapter. The adapter must evaluate candidate code against the same frozen fixtures, fixed thresholds, cameras, seeds and environment. Run the baseline and every candidate with the same tests. It must return a nonzero status on infrastructure failure and write JSON to the supplied output path:

    {"pass": true, "metrics": {"missed_defects": 0, "false_alarms": 2}}

Pass must require all protected regression tests, valid outputs, and complete case coverage; do not interpret a candidate's own gate PASS as proof that a gate change is good. Test clean controls and planted defects independently, including all seven defect categories, drift and fixed/solved cameras. Hidden holdouts must be separate and inaccessible to agents. Freeze the benchmark and adapter before agents begin; do not change metrics after seeing results. If the baseline itself fails the mandatory gate, stop and establish an appropriate baseline rather than weakening requirements.

    python ai_lab/tournament.py evaluate ../figurine-round-01 --config C:/owner-judge/judge.json

The report and per-candidate logs appear in judgments/. Only non-regressing candidates with a strict gain qualify. Priority order breaks unequal tradeoffs between eligible candidates; exact ties get no recommendation. Use stable metrics, not noisy single-run runtimes. The owner reviews all cross-reviews and evidence, then integrates selected commits or individual changes on a separate branch and reruns the full suite on the combination before opening a PR. Never auto-merge an untested combination.

## Security and limitations

Git worktrees are isolation for development, not security sandboxes. They share Git metadata. Run candidate code only in a disposable VM/container without credentials, network access, or writable access to the judge and holdouts. A trusted external adapter must enforce this and produce metrics from independent observations, not agent-authored JSON. The coordinator does not enforce OS isolation, provider budgets, or review completion. Do not run arbitrary candidate code on your credentialed host. Do not give agents access to the external judge directory. This is a manual-session v1; CLI/API dispatch and verified adoption are next steps.

Start from a deliberately selected commit containing the approved shared baseline; main may be behind current research branches. Never overwrite existing Claude/Codex/Gemini branches. Keep results and rejected ideas in improvements/ after review.
