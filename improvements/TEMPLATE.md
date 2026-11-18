---
title: <one line: what it improves>
author: <claude | codex | name>
date: YYYY-MM-DD
status: proposed
applies_to: <e.g. contacts, eyes, thin parts, approval gate, swap planning, slicing>
tool: <path to the code, or "method only">
---

## Problem
What went wrong before: the owner's words, defect crops, which job.

## Method
What the improvement does and why it should work. Give the parameters.

## Evidence (author)
Same mesh, same cameras, before and after:
- Gate numbers from `approved_match.py`, judge and round (clear disagreement %, largest patch, review patches).
- Crops: before | after.
- Regressions checked: `approved_match_selftest.py`, earlier jobs' regression cases, protected features.

## How to use it
The exact command, where it goes in the PLAYBOOK pipeline, and when *not* to use it.

## Trials (other agents append here; never edit someone else's entry)
| Date | Agent | Job | Result (numbers) | Verdict |
|---|---|---|---|---|
