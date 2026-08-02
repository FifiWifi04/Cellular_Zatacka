# Session prompt template

For running tasks as a scheduled/routine agent session (Claude on the web, a
Routine, or any fresh agent). Paste the block below as the session prompt.

It is written to work **unattended**: the agent picks its own task from the board,
so the same prompt can fire repeatedly without editing.

---

## Autonomous prompt (recommended)

```
You are working on the Cellular Zatacka game in this repository.

STEP 1 — Read these two files completely, in this order, before anything else:
  1. docs/AGENT_CONDUCT.md
  2. docs/TASKS.md

STEP 2 — Pick your task. Take the LOWEST-NUMBERED task whose status is READY.
If no task is READY, stop and report which dependencies are blocking, and do
not change any code.

STEP 3 — Read that task's file in docs/tasks/ completely. If it has a
"## Findings" section, answer those questions by reading the code and write the
answers into the task file BEFORE you implement anything.

STEP 4 — Implement exactly that one task. Nothing else. Follow every rule in
AGENT_CONDUCT.md, especially:
  - smallest possible diff; no reformatting, no renames, no drive-by fixes
  - every hazard change goes in BOTH checkCollision() and raycast()
  - collision is always swept, never point-in-time
  - physics state is authoritative; sprites only mirror it
  - no allocation in the per-frame hot path
  - anything you notice outside scope goes in docs/BACKLOG.md, not into the diff

STEP 5 — Verify. Run every numbered item in the task's "## Verification"
section. Serve the folder with `python3 -m http.server 8083` and drive the game
in a real browser (Playwright/Chromium is available in this environment; do not
run `playwright install`). The browser console must be completely clean. If a
check fails, fix it or revert — do not commit a partially working task.

STEP 6 — Commit and push.
  - Update docs/TASKS.md: your task READY -> DONE, and flip any newly unblocked
    task BLOCKED -> READY.
  - One commit containing the code change, the board update, and any BACKLOG
    additions.
  - Commit message format is in AGENT_CONDUCT.md section 9. Include the measured
    numbers the task asked for.
  - Push to the working branch. Do not open a pull request.

STEP 7 — Report back: which task, what changed, what you measured, what you
verified, and anything you added to the backlog.

If the task turns out to be wrong or impossible, do not improvise a different
design. Write a "## Blocked" section at the bottom of the task file explaining
what you found, commit only that, and stop.
```

---

## Targeted variant

When you want a specific task run, replace STEP 2 with:

```
STEP 2 — Your task is T<NN>. Confirm on the board that its dependencies are
DONE. If they are not, stop and report rather than proceeding.
```

---

## Notes for whoever schedules these

- **One task per session.** These tasks each carry real verification work; a
  session that tries two will short-change both.
- **Track A must run in order.** T01 → T02 → T03 touch the same function, and
  T06 needs both T04 and T05.
- **T06 is a gate.** If it returns FAIL, the follow-up tasks it creates must run
  before Track C or D. Do not let a schedule march past a failed gate.
- **Verification needs a browser.** Sessions that cannot run one will produce
  unverified work — which, for this codebase, is worse than no work. If the
  environment lacks a browser, restrict scheduling to documentation-only tasks.
- **Tasks with a `## Findings` section** (T11, T15, T18) depend on reading the
  code before designing. Expect those sessions to take longer.
- **T09, T20, and T05 are independent** — good candidates when the head of every
  other track is blocked.
