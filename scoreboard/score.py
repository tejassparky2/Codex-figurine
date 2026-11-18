"""Referee for the agent competition. Same judge, same settings, every agent's submission.

  score.py run <job> [--practice]      score every '<agent> works/<job>/submission.json' with the job's judge
  score.py owner <job> <agent> accept|defect [--note TEXT] [--first-round]
  score.py adjust <agent> <points> --reason TEXT [--job JOB]
  score.py board                       rebuild SCOREBOARD.md from the ledger

The judge lives in jobs/<job>/judge/judge.json (approved views, referee anchors, masks). Its hash is stored with
every result, so a judge changed after scoring is visible. Rules and point values: scoreboard/RULES.md.
"""
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'scoreboard'
LEDGER = BOARD / 'ledger.json'
GATE = ROOT / 'wedding-u1-skill' / 'coloring' / 'approved_match.py'
POINTS = dict(gate_pass=3, head_to_head_win=2, head_to_head_tie=1, invalid_submission=-1,
              owner_accept=5, first_round_bonus=2, owner_defect=-1)
TIER = {'PASS': 0, 'NEEDS_REVIEW': 1, 'FAIL': 2, 'CANNOT_JUDGE': 3, 'INVALID': 4}


def ledger():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else []


def save(events):
    LEDGER.write_text(json.dumps(events, indent=1) + '\n')
    board()


def agents():
    return sorted(p.name[:-len(' works')] for p in ROOT.iterdir() if p.is_dir() and p.name.endswith(' works'))


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')


def judge_hash(judge_dir):
    h = hashlib.sha256()
    for f in sorted(judge_dir.rglob('*')):
        if f.is_file():
            h.update(f.relative_to(judge_dir).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()[:16]


def run(job, practice):
    judge_dir = ROOT / 'jobs' / job / 'judge'
    judge = json.loads((judge_dir / 'judge.json').read_text())
    practice = practice or not judge.get('official', False)
    jh = judge_hash(judge_dir)
    events = ledger()
    rnd = 1 + max([e['round'] for e in events if e['job'] == job and e.get('kind') == 'gate'] or [0])
    results = {}
    for agent in agents():
        sub_file = ROOT / f'{agent} works' / job / 'submission.json'
        if not sub_file.exists():
            continue
        sub = json.loads(sub_file.read_text())
        guide = (sub_file.parent / sub['finish_guide']).resolve()
        out = BOARD / 'runs' / job / f'round-{rnd}' / agent
        cmd = [sys.executable, '-I', str(GATE), str(guide), str(out)]
        for v in judge['views']:
            cmd += ['--approved', str(judge_dir / v['image']) + (f"@{v['yaw']}" if 'yaw' in v else '')]
            if v.get('mask'):
                cmd += ['--mask', str(judge_dir / v['mask'])]
        if judge.get('prototypes'):
            cmd += ['--prototypes', str(judge_dir / judge['prototypes'])]
        cmd += [str(a) for a in judge.get('gate_args', [])]
        print(f'== {agent}: {guide.relative_to(ROOT)}', flush=True)
        code = subprocess.run(cmd, cwd=ROOT).returncode if guide.exists() else -1
        reports = sorted(out.glob('view*/report.json'))
        if code not in (0, 1, 2, 3) or not reports:
            results[agent] = dict(verdict='INVALID', guide=str(guide.relative_to(ROOT)) if guide.exists() else sub['finish_guide'])
            continue
        reps = [json.loads(r.read_text()) for r in reports]
        verdict = max((r['verdict'] for r in reps), key=TIER.get)
        results[agent] = dict(
            verdict=verdict, guide=str(guide.relative_to(ROOT)), submission_round=sub.get('round'),
            hard_mismatch_pct=round(sum(r['hard_mismatch_pct'] for r in reps) / len(reps), 4),
            largest_clear_error_mm2=max(r.get('largest_clear_error_mm2', r['largest_patch_mm2']) for r in reps),
            review_patches=sum(r.get('review_patches', 0) for r in reps),
            boundary_p95_mm=max(r['boundary_offset_mm']['p95'] for r in reps),
            silhouette_iou=min(r['silhouette_iou'] for r in reps))
    if not results:
        raise SystemExit(f'No submissions for {job}. Each agent adds "<agent> works/{job}/submission.json".')
    # Rank: verdict tier, then clear disagreement, then the largest clear error.
    key = {a: (TIER[r['verdict']], r.get('hard_mismatch_pct', 99), r.get('largest_clear_error_mm2', 1e9)) for a, r in results.items()}
    new = []

    def award(agent, pts, reason):
        new.append(dict(kind='gate', date=now(), job=job, round=rnd, agent=agent, points=0 if practice else pts,
                        would_be_points=pts, practice=practice, reason=reason, judge_hash=jh, metrics=results[agent]))

    for a, r in results.items():
        if r['verdict'] == 'INVALID':
            award(a, POINTS['invalid_submission'], 'submission missing, unreadable or not a single painted mesh')
        elif r['verdict'] == 'PASS':
            award(a, POINTS['gate_pass'], 'approval gate PASS on every judge view')
        else:
            award(a, 0, f"gate {r['verdict']}")
    ranked = sorted((a for a in results if results[a]['verdict'] not in ('INVALID', 'CANNOT_JUDGE')), key=key.get)
    if len(ranked) >= 2:
        best, second = ranked[0], ranked[1]
        kb, ks = key[best], key[second]
        tie = kb[0] == ks[0] and abs(kb[1] - ks[1]) <= max(.02, .05 * max(kb[1], ks[1]))
        if tie:
            for a in ranked[:2]:
                award(a, POINTS['head_to_head_tie'], f'head-to-head tie with {ranked[1] if a == ranked[0] else ranked[0]}')
        else:
            award(best, POINTS['head_to_head_win'], f'head-to-head win over {", ".join(ranked[1:])}')
    events += new
    save(events)
    for e in new:
        print(f"{e['agent']}: {e['reason']} -> {e['points']} points" + (f" (practice; would be {e['would_be_points']})" if practice else ''))


def owner(job, agent, verdict, note, first_round):
    events = ledger()
    if verdict == 'accept':
        events.append(dict(kind='owner', date=now(), job=job, agent=agent, points=POINTS['owner_accept'], reason=f'owner accepted delivery. {note}'.strip()))
        if first_round:
            events.append(dict(kind='owner', date=now(), job=job, agent=agent, points=POINTS['first_round_bonus'], reason='accepted in the first review round'))
    else:
        events.append(dict(kind='owner', date=now(), job=job, agent=agent, points=POINTS['owner_defect'],
                           reason=f'owner found a defect the agent missed: {note}'))
    save(events)


def adjust(agent, pts, reason, job):
    events = ledger()
    events.append(dict(kind='adjust', date=now(), job=job or '-', agent=agent, points=pts, reason=reason))
    save(events)


def board():
    events = ledger()
    names = sorted(set(agents()) | {e['agent'] for e in events})
    total = {a: sum(e['points'] for e in events if e['agent'] == a) for a in names}
    lines = ['# Scoreboard', '', 'Generated by `scoreboard/score.py` from `ledger.json`. Rules: [RULES.md](RULES.md). Do not edit by hand.', '',
             '| Agent | Points | Owner accepts | Owner-found defects | Gate PASSes |', '|---|---:|---:|---:|---:|']
    for a in sorted(names, key=lambda a: -total[a]):
        mine = [e for e in events if e['agent'] == a]
        lines.append(f"| {a} | {total[a]} | {sum(e['reason'].startswith('owner accepted') for e in mine)} | "
                     f"{sum(e['reason'].startswith('owner found') for e in mine)} | "
                     f"{sum(e.get('kind') == 'gate' and not e.get('practice') and 'PASS' in e['reason'] for e in mine)} |")
    lines += ['', '## Gate rounds', '', '| Date | Job | Round | Agent | Verdict | Clear disagreement % | Largest clear error mm² | Review patches | Points | Note |',
              '|---|---|---:|---|---|---:|---:|---:|---:|---|']
    for e in events:
        if e.get('kind') != 'gate':
            continue
        m = e['metrics']
        pts = f"{e['points']}" + (f" (practice, would be {e['would_be_points']})" if e.get('practice') else '')
        lines.append(f"| {e['date']} | {e['job']} | {e['round']} | {e['agent']} | {m['verdict']} | {m.get('hard_mismatch_pct', '')} | "
                     f"{m.get('largest_clear_error_mm2', '')} | {m.get('review_patches', '')} | {pts} | {e['reason']} |")
    other = [e for e in events if e.get('kind') != 'gate']
    if other:
        lines += ['', '## Owner verdicts and adjustments', '', '| Date | Job | Agent | Points | Reason |', '|---|---|---|---:|---|']
        lines += [f"| {e['date']} | {e['job']} | {e['agent']} | {e['points']} | {e['reason']} |" for e in other]
    (BOARD / 'SCOREBOARD.md').write_text('\n'.join(lines) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest='cmd', required=True)
    r = sp.add_parser('run')
    r.add_argument('job')
    r.add_argument('--practice', action='store_true')
    o = sp.add_parser('owner')
    o.add_argument('job')
    o.add_argument('agent')
    o.add_argument('verdict', choices=['accept', 'defect'])
    o.add_argument('--note', default='')
    o.add_argument('--first-round', action='store_true')
    a = sp.add_parser('adjust')
    a.add_argument('agent')
    a.add_argument('points', type=int)
    a.add_argument('--reason', required=True)
    a.add_argument('--job')
    sp.add_parser('board')
    args = p.parse_args()
    if args.cmd == 'run':
        run(args.job, args.practice)
    elif args.cmd == 'owner':
        owner(args.job, args.agent, args.verdict, args.note, args.first_round)
    elif args.cmd == 'adjust':
        adjust(args.agent, args.points, args.reason, args.job)
    else:
        board()


if __name__ == '__main__':
    main()
