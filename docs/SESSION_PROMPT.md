# Session prompt template

For running tasks as a scheduled/routine agent session (Claude on the web, a
Routine, or any fresh agent).

Two variants below. **The Routine prompt is the one to use for scheduled runs** —
it is fully standalone, because each firing starts a fresh session with no memory
of the last one.

---

## A. Routine prompt (scheduled, fresh session each firing)

Paste this verbatim as the Routine's prompt. It never needs editing between
firings — the agent picks its own task from the board.

```
Repository: FifiWifi04/Cellular_Zatacka
Branch: claude/html-game-phase-1-43obou  (work here, never push to main)

You are implementing ONE task from this project's task board, then stopping.
This is a scheduled session with no memory of previous runs — everything you
need is in the repository.

STEP 0 — SYNC AND SANITY CHECK
  - git fetch origin and check out the branch above, then pull it.
  - Run `git log --oneline -10` and `git status`.
  - If the working tree is dirty, a previous session failed mid-task. Do not
    build on it: report what you found, and stop.

STEP 1 — READ THE RULES
  Read completely, in this order, before touching any code:
    1. docs/AGENT_CONDUCT.md      <- the rules and the five traps in this codebase
    2. docs/TASKS.md              <- the status board
  Do not skip these because the task looks simple. They exist because specific
  mistakes have already happened in this codebase.

STEP 2 — PICK YOUR TASK
  Take the LOWEST-NUMBERED task on the board whose status is READY.
  Before starting it, confirm it has not already been done: search
  `git log --oneline` for a commit starting with that task's ID (e.g. "T04:").
  If such a commit exists, the board is stale — fix the board, push that fix
  alone, and stop.
  If no task is READY, stop and report which dependencies are blocking.

STEP 3 — READ THE TASK
  Read docs/tasks/<ID>-*.md completely.
  If it has a "## Findings" section, answer those questions by reading the game
  code and write the answers into the task file BEFORE designing anything. Those
  questions exist because their answers change the implementation.
  Line numbers in task files are approximate — anchor on function names and the
  quoted search strings.

STEP 4 — IMPLEMENT EXACTLY THAT ONE TASK
  Nothing else. Follow AGENT_CONDUCT.md, in particular:
    - smallest possible diff; no reformatting, no renames, no drive-by fixes
    - any hazard change goes in BOTH checkCollision() and raycast()
    - collision is always swept, never point-in-time
    - physics state is authoritative; visuals only mirror it
    - no allocation in the per-frame hot path
    - anything you notice outside scope goes in docs/BACKLOG.md, not the diff

STEP 5 — VERIFY IN A REAL BROWSER
  Serve the folder: python3 -m http.server 8083
  Drive 260703_Cellsnake.html with Playwright/Chromium, which is preinstalled —
  do NOT run `playwright install`.
  Run EVERY numbered item in the task's "## Verification" section, and capture
  the measurements it asks for (timings, counts, before/after numbers).
  The browser console must be completely clean. If a check fails, fix it or
  revert — never commit a partially working task.

STEP 6 — COMMIT AND PUSH
  - Update docs/TASKS.md: your task READY -> DONE, and flip any newly unblocked
    task BLOCKED -> READY.
  - ONE commit containing the code change, the board update, and any BACKLOG
    additions. Message format is in AGENT_CONDUCT.md section 9; include the
    numbers you measured.
  - git push -u origin claude/html-game-phase-1-43obou
  - Do NOT open a pull request.

STEP 7 — REPORT
  State: which task, what changed, what you measured, what you verified, what
  you added to the backlog, and which task is now next.

STOP CONDITIONS — stop and report rather than pressing on:
  - The task turns out to be wrong or impossible. Do not improvise a different
    design: write a "## Blocked" section at the bottom of the task file saying
    what you found, commit only that, and stop.
  - Verification cannot be completed (no browser, no network). Unverified work
    on this codebase is worse than no work — commit nothing.
  - The task file says the step needs an owner decision.
  - T06 returns a FAIL verdict. Create the follow-up task files it calls for,
    put them on the board ahead of T07, and stop. Do not start Track C or D on
    a failed Phase 1 gate.
```

---

## B. Targeted variant

When you want a specific task run, replace STEP 2 with:

```
STEP 2 — Your task is T<NN>. Confirm on the board that its dependencies are
DONE. If they are not, stop and report rather than proceeding.
```

---

## Scheduling notes

**Cadence.** Every **6 hours** (4 tasks/day) is the recommended setting. Every 3
hours works mechanically, but several tasks need a human to look at the result
before the next one builds on it, and at 8 tasks/day the whole 21-task board is
consumed in under three days with no review window. 6h finishes Phase 1 in about
a day and a half and still leaves room to inspect.

**Sessions must not overlap.** Some tasks are long — T06 alone runs three
30-minute soak tests. If a firing is still running when the next one fires, the
second will see a dirty tree or a stale board. Step 0 catches this and stops
safely, but the firing is wasted. Prefer 6h for that reason too.

**Tasks that will stop and ask.** Do not expect these to complete unattended:

| Task | Why it needs you |
|---|---|
| T06 | Produces a PASS/FAIL gate verdict. A FAIL must not be worked around. |
| T07 | The trace cap is a real gameplay change. The task defaults to a conservative memory-bound value and asks before shipping the aggressive one. |
| T12 | Highest-risk task on the board — it changes the arena boundary. Worth reviewing personally. |
| T21 | Acceptance is subjective. "Revert it, it looked worse" is a valid outcome and needs your eye. |
| P01 | Parked. Must never be picked up. |

**Order matters in Track A.** T01 → T02 → T03 all edit the same function, and T06
needs both T04 and T05. The board enforces this through the READY/BLOCKED
statuses — do not hand-edit statuses to parallelise.

**If a session stops with nothing done**, that is the design working. Read its
report, resolve the blocker, and the next firing will pick up from the board.
