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

STEP 0 — SYNC, AND CONFIRM YOU CAN SEE THE PLAN
  - git fetch origin --prune
  - Check out the working branch, creating it from origin if it is not local:
      git checkout claude/html-game-phase-1-43obou 2>/dev/null \
        || git checkout -b claude/html-game-phase-1-43obou origin/claude/html-game-phase-1-43obou
      git pull --ff-only origin claude/html-game-phase-1-43obou
    A fresh session may start on some other auto-generated branch. Do not work
    there. Everything below assumes the branch above.
  - CONFIRM docs/AGENT_CONDUCT.md and docs/TASKS.md both exist. If either is
    missing, you are on the wrong branch or the clone is incomplete: STOP and
    report. Do not proceed, and do not improvise a plan of your own.
  - Run `git log --oneline -10` and `git status`. If the working tree is dirty,
    a previous session failed mid-task. Do not build on it: report and stop.

STEP 1 — READ THE RULES
  Read completely, in this order, before touching any code:
    1. docs/AGENT_CONDUCT.md      <- the rules and the five traps in this codebase
    2. docs/TASKS.md              <- the status board
  Do not skip these because the task looks simple. They exist because specific
  mistakes have already happened in this codebase.

STEP 2 — PICK YOUR TASK
  Take the LOWEST-NUMBERED task on the board whose status is READY.
  SKIP any task marked OWNER-RUN (currently T06) — those need a human and a
  longer runtime than you have; take the next READY task instead.
  If no task is READY, stop and report which dependencies are blocking, and
  name any OWNER-RUN task that is waiting on the owner.

  Then open docs/tasks/<ID>-*.md and check whether it has a "## Progress"
  section:

  - NO "## Progress" (the normal case, one session per task):
      Confirm the task has not already been done — search `git log --oneline`
      for a commit starting with that task's ID (e.g. "T04:"). If such a commit
      exists, the board is stale: fix the board, push that fix alone, and stop.

  - HAS "## Progress" (a RESUMABLE multi-session task, e.g. T06):
      Partial commits with that task's ID are EXPECTED and do not mean the board
      is stale. Do not apply the check above. Read the checklist, start at the
      first unticked stage, and follow that task file's own "How to run this task
      across sessions" instructions instead of STEP 6 below.

STEP 3 — READ THE TASK
  Read docs/tasks/<ID>-*.md completely.
  If it has a "## Findings" section, answer those questions by reading the game
  code and write the answers into the task file BEFORE designing anything. Those
  questions exist because their answers change the implementation.
  Line numbers in task files are approximate — anchor on function names and the
  quoted search strings.
  Never begin a timed run you cannot finish inside this session. A truncated
  measurement is worse than none — stop and leave the stage for the next firing.

STEP 4 — IMPLEMENT EXACTLY THAT ONE TASK
  Nothing else. Follow AGENT_CONDUCT.md, in particular:
    - smallest possible diff; no reformatting, no renames, no drive-by fixes
    - any hazard change goes in BOTH checkCollision() and raycast()
    - collision is always swept, never point-in-time
    - physics state is authoritative; visuals only mirror it
    - no allocation in the per-frame hot path
    - anything you notice outside scope goes in docs/BACKLOG.md, not the diff

STEP 5 — VERIFY IN A REAL BROWSER (you have Bash only — there is no browser tool)
  USE THE EXISTING HARNESS. Do not write browser boilerplate from scratch:
  tools/verify_harness.py already handles serving the game, launching the
  sandbox's Chromium, capturing console/page errors, starting a round with the
  right configuration, and advancing GAME time. Read its docstring — it
  documents four traps that will otherwise silently invalidate your results.

  5a. One-time setup if needed:  pip install playwright
      Do NOT run `playwright install` — its download hosts are blocked, and a
      Chromium is already present. The harness globs for it.
      Smoke-test the harness first:  python3 tools/verify_harness.py

  5b. Write a SHORT script per check that imports the harness:
        import sys; sys.path.insert(0, "tools")
        from verify_harness import game
        with game(players=1, bots=1) as g:
            g.run_game_seconds(30)
            print(g.stats())
            g.screenshot("after30s")
            g.assert_console_clean()

  5c. Run each script via Bash SYNCHRONOUSLY, UNDER 10 MINUTES per invocation —
      that is your hard command ceiling. Split long checks across several short
      scripts. Never start a run you cannot finish inside that ceiling.

  5d. Read the printed JSON, and use the Read tool on /tmp/verify/*.png to
      inspect screenshots visually — Read renders images.

  Run EVERY numbered item in the task's "## Verification" section and capture
  the measurements it asks for (timings, counts, before/after numbers).
  The console must be clean — the harness already ignores the browser's
  automatic favicon.ico 404, which is the only expected entry; treat anything
  else as a real failure.
  If a check fails, fix it or revert — never commit a partially working task.

STEP 6 — COMMIT AND PUSH
  (Resumable tasks override this — commit per stage as their task file says,
  and leave the board at READY until the final stage.)
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
  - docs/AGENT_CONDUCT.md or docs/TASKS.md is missing after STEP 0. You are on
    the wrong branch — report it, change nothing.
  - Verification cannot be completed (no Playwright, no Chromium, no network).
    Unverified work on this codebase is worse than no work: record why in
    docs/BACKLOG.md, commit only that, and stop.
  - The task file says the step needs an owner decision.
  - The only remaining work is OWNER-RUN (T06). Report that it is waiting on
    the owner and stop. Do not attempt it, and do not start Track C or D on an
    unfinished Phase 1 gate.
```

---

## B. Targeted variant

When you want a specific task run, replace STEP 2 with:

```
STEP 2 — Your task is T<NN>. Confirm on the board that its dependencies are
DONE. If they are not, stop and report rather than proceeding.
```

---

## Environment requirements

Learned the hard way — the first routine produced no-ops for these reasons:

- **`docs/` must exist on whatever branch the session lands on.** A scheduled
  session starts on an auto-generated branch cut from the repo default, not on
  your working branch. `docs/` is therefore merged to `main`; STEP 0 also
  force-checks-out the working branch and aborts loudly if the docs are absent.
- **Minimum `allowed_tools`:** `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`.
  STEP 5 is written to need nothing more — it drives Playwright through Bash.
  Adding `BashOutput` and `KillBash` would let sessions manage long background
  processes and is worth doing if you can.
- **Commands are capped at 10 minutes.** Anything longer must be split, or
  marked `OWNER-RUN` on the board (currently only T06).
- **Repo write access.** The session must be able to push to
  `claude/html-game-phase-1-43obou`.

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
| T06 | **`OWNER-RUN` — scheduled sessions skip it entirely.** Its 30-minute soaks exceed the 10-minute command ceiling, and it ends in a PASS/FAIL gate verdict that is yours to make. Run it interactively. Note that T07, T11 and T16 stay `BLOCKED` until you do, so the routine will run out of Track A work and fall through to T09/T20/T21. |
| T07 | The trace cap is a real gameplay change. The task defaults to a conservative memory-bound value and asks before shipping the aggressive one. |
| T12 | Highest-risk task on the board — it changes the arena boundary. Worth reviewing personally. |
| T21 | Acceptance is subjective. "Revert it, it looked worse" is a valid outcome and needs your eye. |
| P01 | Parked. Must never be picked up. |

**Order matters in Track A.** T01 → T02 → T03 all edit the same function, and T06
needs both T04 and T05. The board enforces this through the READY/BLOCKED
statuses — do not hand-edit statuses to parallelise.

**If a session stops with nothing done**, that is the design working. Read its
report, resolve the blocker, and the next firing will pick up from the board.
