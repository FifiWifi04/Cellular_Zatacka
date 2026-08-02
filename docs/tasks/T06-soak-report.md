# T06 — Soak run + memory profile (Phase 1 gate evidence)

**Track:** A (Phase 1 gate) · **Depends on:** T04, T05 · **Risk:** none (no gameplay code) · **Est. diff:** report only

Read `docs/AGENT_CONDUCT.md` before starting.

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

### Step 1 — Build the driver

Extend `run_test.py` (or add `soak_test.py` beside it — your choice, but keep it
Python + Selenium to match what exists). It must:

1. Fix the hard-coded Windows paths already in `run_test.py` — use paths relative
   to the script's own directory.
2. Serve the folder and open the game in headless Chrome with
   `--enable-precise-memory-info` and `--window-size=1280,1024`.
3. Set up the run via `execute_script`:
   `devMode = true; godMode = false; fuzzActive = true; currentMode = 1; aiCount = 3; startRound();`
4. Every 10 seconds, read `window.fuzzStats` via `driver.execute_script("return window.fuzzStats")`
   and append a row to a CSV.
5. Also capture `driver.get_log('browser')` each sample and record any
   `SEVERE` entries verbatim.
6. Run for **30 minutes**. Save a screenshot every 5 minutes as a visual sanity
   check.
7. Write `docs/reports/soak-<YYYYMMDD>.csv` and the screenshots to
   `docs/reports/soak-<YYYYMMDD>/`.

### Step 2 — Run three configurations

| Run | Config | Purpose |
|---|---|---|
| A | `godMode=false`, 1 human + 3 bots, Normal speed | The real soak — rounds cycle constantly |
| B | `godMode=true`, 1 human + 3 bots, Very Fast | Maximum trace growth; nothing dies, so traces grow unbounded — this is the stress case for the grid rebuild |
| C | `godMode=false`, split-screen camera, 4 players | Exercises the `RenderTexture` path T05 touched |

Run B is the important one for trace/grid cost. Expect it to degrade — that is
the finding that justifies T07, not a failure.

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

### Step 4 — Write the report

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
- `docs/reports/soak-*.csv` and screenshots (new)
- `docs/TASKS.md` status update

**No changes to `260703_Cellsnake.html`.** If you feel the need to change it, you
have found a bug — write it up instead.

---

## Verification

1. All three runs completed the full 30 minutes without the driver crashing.
2. CSVs exist, are non-empty, and have a row roughly every 10s.
3. The report states a verdict in its first line and every claim in it is backed
   by a number in the CSV.
4. Screenshots at 30 minutes show a game that still renders correctly.

## Definition of done

- [ ] Driver script committed, no hard-coded absolute paths
- [ ] Three 30-minute runs completed, CSVs + screenshots committed
- [ ] `docs/reports/PHASE1-GATE.md` written with an explicit PASS/FAIL
- [ ] `errors == 0` in run A and C, or the failures documented and a follow-up
      task file created
- [ ] No gameplay code changed
- [ ] `docs/TASKS.md`: T06 → `DONE`; T07, T11, T16 → `READY`

## If the verdict is FAIL

Do not fix it in this session. Create the follow-up task file(s) under
`docs/tasks/`, add them to the board as `READY` ahead of T07, and leave Phase 1
open. The gate exists to be honest about, not to be passed.
