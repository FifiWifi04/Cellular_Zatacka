# T06 — Soak run + memory profile (Phase 1 gate evidence)

**Track:** A (Phase 1 gate) · **Depends on:** T04, T05 · **Risk:** none (no gameplay code) · **Est. diff:** report only

**👤 OWNER-RUN — a scheduled agent session must SKIP this task** and take the
next `READY` one instead. Each soak is a continuous 30-minute run, and a
scheduled session's commands are capped at 10 minutes, so it physically cannot
complete a stage. Run this yourself, interactively, when the board reaches it.
It also ends in a PASS/FAIL gate verdict that is yours to make.

**⚠ This task is RESUMABLE and spans multiple sessions.** It runs 90+ minutes of
soak tests. Read `## Progress` below **first**: it is the durable record of what
has already been done, and it is committed after every stage.

Read `docs/AGENT_CONDUCT.md` before starting.

---

## How to run this task across sessions

This task breaks the normal "one task, one commit" rule, deliberately. Each stage
is committed on completion so an interrupted session loses at most one stage
instead of all of them.

1. Read `## Progress`. Find the first stage that is not `[x]`.
2. Do **only that stage**.
3. Tick it in `## Progress`, commit (message `T06: <stage name>`), and push.
4. If session budget clearly allows another full stage, continue to the next one.
   If not, stop and report which stage is next. **Never start a 30-minute run you
   cannot finish** — a truncated CSV is worse than no CSV.
5. Leave T06 as `READY` on the board until **every** stage is ticked. Only the
   session that completes the final stage flips it to `DONE`.

Partial `T06:` commits in the git log are expected and do **not** mean the board
is stale.

---

## Progress

- [ ] **Stage 0 — driver.** `run_test.py` paths fixed / `soak_test.py` written,
      committed, and smoke-tested with a 2-minute run that produces a valid CSV.
- [ ] **Stage A — run A.** 30 min, `godMode=false`, 1 human + 3 bots, Normal.
      CSV + screenshots committed.
- [ ] **Stage B — run B.** 30 min, `godMode=true`, 1 human + 3 bots, Very Fast.
      CSV + screenshots committed.
- [ ] **Stage C — run C.** 30 min, `godMode=false`, split-screen, 4 players.
      CSV + screenshots committed.
- [ ] **Stage D — analysis + report.** `docs/reports/PHASE1-GATE.md` written from
      the three CSVs, with an explicit PASS/FAIL verdict. Board updated.

*(Record the commit SHA and browser version alongside each stage as you tick it —
the report needs them, and a later session will not have them otherwise.)*

---

## Goal

Run the fuzzer for its actual purpose and produce the written evidence that
Phase 1 is "mathematically stable and performance-tested". The deliverable is a
committed report, not a code change.

## Why

The roadmap forbids advancing to a new phase until the current one is stable and
performance-tested. Phases 1.1 and 1.2 are now built (T01–T05), but nothing has
been *measured over time*. The specific risk is PixiJS display-object lifecycle
across rapid `startRound()` calls — T05 fixed the known sites, and this task
proves there are no unknown ones.

**This task must not change gameplay code.** If it finds a bug, write it up, open
a follow-up task file, and stop. Fixing it is a separate session.

---

## Prerequisites

- T04 done: `window.fuzzStats` exists with `rounds`, `elapsed`, `tracePoints`,
  `gridCells`, `worldChildren`, `vesicles`, `organelles`, `virusParticles`,
  `heapMB`, `errors`.
- T05 done: teardown is correct.
- Chrome or Chromium (the run needs `performance.memory`, which is
  Chrome-only). Launch with `--enable-precise-memory-info` for useful heap
  numbers.

---

## Procedure

### Step 1 — Build the driver *(Stage 0)*

Extend `run_test.py` (or add `soak_test.py` beside it — your choice, but keep it
Python + Selenium to match what exists). It must:

1. Fix the hard-coded Windows paths already in `run_test.py` — use paths relative
   to the script's own directory.
2. **Take the run label as a command-line argument**: `python3 soak_test.py A`.
   One invocation runs exactly one configuration, so a session can complete one
   stage and stop cleanly. Hard-code the three configs in a dict keyed by label.
3. **Take an optional duration argument** (`--minutes`, default 30) so Stage 0's
   smoke test can run 2 minutes with the identical code path.
4. Serve the folder and open the game in headless Chrome with
   `--enable-precise-memory-info` and `--window-size=1280,1024`.
5. Set up the run via `execute_script`, using the selected config, e.g. run A:
   `devMode = true; godMode = false; fuzzActive = true; currentMode = 1; aiCount = 3; startRound();`
6. Every 10 seconds, read `window.fuzzStats` via
   `driver.execute_script("return window.fuzzStats")`, append a row to the CSV,
   and **flush to disk immediately**. Never buffer — a killed session must leave
   whatever it collected on disk.
7. Also capture `driver.get_log('browser')` each sample and record any `SEVERE`
   entries verbatim to a sidecar log.
8. Save a screenshot every 5 minutes.
9. **On successful completion only**, write a marker file
   `docs/reports/soak-<label>/COMPLETE` containing the elapsed duration, the
   commit SHA, and the browser version.

**The marker file is what makes this task resumable.** A CSV without a sibling
`COMPLETE` is a truncated run: it must be deleted and the stage re-run, never
analysed. State that rule in the driver's own docstring so the next session cannot
miss it.

Output layout, one directory per run:

```
docs/reports/soak-A/  { soak.csv, console.log, frame-*.png, COMPLETE }
docs/reports/soak-B/  ...
docs/reports/soak-C/  ...
```

Finish Stage 0 by running `--minutes 2` against config A and confirming the CSV,
screenshots, and `COMPLETE` marker all appear. Commit the driver **and** delete
the smoke-test output — it is not evidence.

### Step 2 — Run three configurations *(Stages A, B, C — one per stage)*

| Run | Config | Purpose |
|---|---|---|
| A | `godMode=false`, 1 human + 3 bots, Normal speed | The real soak — rounds cycle constantly |
| B | `godMode=true`, 1 human + 3 bots, Very Fast | Maximum trace growth; nothing dies, so traces grow unbounded — this is the stress case for the grid rebuild |
| C | `godMode=false`, split-screen camera, 4 players | Exercises the `RenderTexture` path T05 touched |

Run B is the important one for trace/grid cost. Expect it to degrade — that is
the finding that justifies T07, not a failure.

**Each run is its own stage.** Complete one, verify its `COMPLETE` marker exists,
commit that run's directory, tick the stage in `## Progress`, push. Then decide
whether there is budget for the next one.

If a run is interrupted: delete its directory entirely and leave the stage
unticked. Do not commit partial data, and do not try to stitch two partial runs
together — the whole point is a continuous 30-minute window.

### Step 3 — Analyse

For each run, plot or tabulate against elapsed time:

- `heapMB` — is it monotonically increasing, or sawtoothing around a stable mean?
  A sawtooth is healthy. A staircase that never returns to its floor is a leak.
- `worldChildren` — must be flat across rounds. Any upward trend is a leak T05
  missed; identify which container by adding a per-container breakdown.
- `tracePoints` and `gridCells` — expected to grow within a round and reset
  between rounds. In run B they grow without bound; record the rate.
- `errors` — must be 0. Any non-zero value blocks the gate.
- Frame timing — if `run_test.py` can sample it, record mean frame time at 0, 10,
  20, 30 minutes.

### Step 4 — Write the report *(Stage D)*

Do this only when Stages A, B and C are all ticked and all three `COMPLETE`
markers exist. Stage D is analysis of committed data — it needs no browser and
should finish comfortably inside one session.

Create `docs/reports/PHASE1-GATE.md` containing:

1. **Verdict** — PASS or FAIL against the gate, stated in the first line.
2. **Setup** — commit SHA, browser version, machine, each run's config.
3. **Results table** — the metrics above at 0/5/10/20/30 min for each run.
4. **Leak analysis** — explicit statement on `worldChildren` and `heapMB`
   trajectory per run, with the numbers.
5. **`undefined` / error log** — every `SEVERE` console entry, or "none".
6. **Performance** — bot raycast timing (from T01's commit message), grid rebuild
   cost vs. trace count from run B, frame time drift.
7. **Findings** — each issue as a numbered item with a proposed task ID. If run B
   shows the grid rebuild becoming a hotspot, say so and point at T07.
8. **Sign-off** — which of roadmap 1.1 and 1.2's bullet points are now
   demonstrably satisfied, quoted from `Development_plan.md`.

---

## Files touched

- `run_test.py` (paths fixed) and/or new `soak_test.py`
- `docs/reports/PHASE1-GATE.md` (new)
- `docs/reports/soak-{A,B,C}/` — CSV, console log, screenshots, `COMPLETE` (new)
- `docs/tasks/T06-soak-report.md` — the `## Progress` checklist, ticked per stage
- `docs/TASKS.md` status update (final stage only)

**No changes to `260703_Cellsnake.html`.** If you feel the need to change it, you
have found a bug — write it up instead.

---

## Verification

1. All three runs completed the full 30 minutes without the driver crashing, and
   each has a `COMPLETE` marker.
2. No orphaned partial run directories are committed.
3. CSVs exist, are non-empty, and have a row roughly every 10s.
4. The report states a verdict in its first line and every claim in it is backed
   by a number in the CSV.
5. Screenshots at 30 minutes show a game that still renders correctly.
6. `## Progress` is fully ticked, with commit SHA and browser version recorded
   per stage.

## Definition of done

- [ ] Driver script committed, no hard-coded absolute paths, takes a run label
      and `--minutes`, flushes each sample, writes `COMPLETE` only on success
- [ ] Three 30-minute runs completed, each with a `COMPLETE` marker, committed
- [ ] `docs/reports/PHASE1-GATE.md` written with an explicit PASS/FAIL
- [ ] `errors == 0` in run A and C, or the failures documented and a follow-up
      task file created
- [ ] No gameplay code changed
- [ ] `## Progress` fully ticked
- [ ] `docs/TASKS.md`: T06 → `DONE`; T07, T11, T16 → `READY`
      *(final stage only — leave T06 `READY` while any stage is outstanding)*

## If the verdict is FAIL

Do not fix it in this session. Create the follow-up task file(s) under
`docs/tasks/`, add them to the board as `READY` ahead of T07, and leave Phase 1
open. The gate exists to be honest about, not to be passed.
