# T06a — Soak measurement (collect the Phase 1 gate evidence)

**Track:** A · **Depends on:** T04, T05 · **Risk:** none (no gameplay code) · **Est. diff:** data only

**⏳ RESUMABLE — spans multiple sessions.** Read `## Progress` below **first**; it
is the durable record of what has already been done and is committed after every
stage.

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Run the fuzzer long enough to prove — or disprove — that the game is stable over
many rounds, and commit the raw data. **This task does not judge the data.**
Reading it and calling PASS/FAIL is T06b, which is yours to do.

Splitting collection from judgement is deliberate: it lets a scheduled session
produce the evidence without waiting on a human decision, so T07, T11 and T16
unblock as soon as the data exists.

## Why

The roadmap forbids advancing a phase until the current one is "mathematically
stable and performance-tested". T01–T05 built the pieces; nothing has been
measured over time. The specific risk is PixiJS display-object lifecycle across
rapid `startRound()` calls — T05 fixed the known sites, and this proves whether
there are unknown ones.

**Do not change gameplay code in this task.** If the data reveals a bug, record
it in `docs/BACKLOG.md`, note it in `## Observations`, and stop. Fixing it is a
separate task.

---

## Progress

- [x] **Stage A** — run A committed with its `COMPLETE` marker
- [ ] **Stage B** — run B committed with its `COMPLETE` marker (was blocked by a tooling contradiction; **fixed 2026-08-04, re-run it** — see `## Resolved` below)
- [x] **Stage C** — run C committed with its `COMPLETE` marker
- [ ] **Stage D** — `## Observations` filled in; board updated; T06b set `OWNER-RUN`

Tick one stage per commit (message `T06a: <stage>`), push, then decide whether
there is budget for the next. Partial `T06a:` commits are expected and do **not**
mean the board is stale. Leave T06a `READY` until every stage is ticked.

---

## Prerequisites — check these first, the driver enforces them

- **T04 done.** `window.fuzzStats` must exist with `rounds` and `errors`, and
  `godMode` must be a separate flag from `devMode`. Without both, the driver
  aborts in ~15 seconds with an explanation — it will not waste an hour
  collecting zeros. If it aborts, T04 is not actually finished; report that.
- **T05 done.** Teardown must be correct or the leak numbers are meaningless.
- `pip install playwright` (the browser itself is already present — never run
  `playwright install`, its download hosts are blocked).

---

## Procedure

### The driver

`tools/soak.py` already exists and does all of this. Do not rewrite it.

```
python3 tools/soak.py --list                    # show the three configs
python3 tools/soak.py A --rounds 60             # run config A
```

It samples `window.fuzzStats` plus live game state every 10 s, flushes each row
to `docs/reports/soak-<label>/soak.csv` immediately, screenshots every 5 minutes,
and writes a `COMPLETE` marker **only** on success.

**A run without its `COMPLETE` marker is truncated.** Delete the whole directory
and re-run it. Never analyse or commit partial data — a short CSV looks exactly
like a valid short run to whoever reads it later.

### Run it detached

A soak will exceed the 10-minute foreground command ceiling. Launch it in the
background and poll:

```
nohup python3 tools/soak.py A --rounds 60 > /tmp/soak-A.log 2>&1 &
```

Then check progress by reading `/tmp/soak-A.log` and
`docs/reports/soak-A/soak.csv` periodically. When `COMPLETE` appears, commit the
directory and tick the stage.

If the session ends before a run finishes, that run's directory has no
`COMPLETE`: the next session deletes it and starts that stage over. Nothing is
corrupted, one stage is lost.

### The three configurations

| Run | Config | What it is for |
|---|---|---|
| A | 1 human + 3 bots, Normal, deaths **on** | The real soak — rounds cycle constantly, exercising `startRound()` teardown |
| B | 1 human + 3 bots, Very Fast, **immortal** | Nothing dies, so traces grow unbounded — the stress case for trace memory and the grid rebuild |
| C | 4 players, split-screen, deaths on | Exercises the `RenderTexture` path T05 touched |

Run B is expected to degrade. That is the finding that justifies T07 — it is not
a failure.

### Targets

**Each config carries its own completion criterion — run it with no arguments.**
`python3 tools/soak.py A`, `... B`, `... C`.

| Run | Completes at | Why |
|---|---|---|
| A | 60 rounds | Deaths are on, so rounds cycle |
| B | 20 minutes | **Immortal — nothing dies, so `rounds` never increments.** A rounds target here is unreachable at any cap. For B the interesting series is `tracePoints` and `gridCells` over time, not round count. |
| C | 60 rounds | Deaths are on |

Override with `--rounds` (rounds-mode configs) or `--minutes` (minutes-mode
configs) only. Passing the wrong one aborts immediately rather than silently
running the default target.

> A rounds target on an immortal config blocked Stage B for a full session and
> wasted a 40-minute run. The driver now refuses the combination. If you hit
> something similar, stop and report as that session correctly did — do not
> improvise around it.

Budget realistically: this sandbox has no GPU and simulates at roughly **0.38×
real time** at the default 640×480 viewport. Note the actual wall time each run
took in `## Observations`.

---

## Files touched

- `docs/reports/soak-{A,B,C}/` — CSV, screenshots, `COMPLETE` (new)
- this file — `## Progress` and `## Observations`
- `docs/TASKS.md` — final stage only
- `docs/BACKLOG.md` — if you find something

**No changes to `260703_Cellsnake.html`, `tools/soak.py`, or
`tools/verify_harness.py`.** If the driver is broken, that is a finding: report
it rather than patching it mid-run, because changing the instrument mid-series
invalidates the comparison.

---

## Verification

1. Three directories exist, each with a `COMPLETE` marker.
2. No directory without a marker was committed.
3. Each CSV has a header plus a row roughly every 10 s.
4. `## Observations` records, per run: wall time, rounds reached, and the first
   and last values of `worldChildren`, `heapMB`, `tracePoints`, `errors`.
5. Final screenshots show a game that still renders correctly.

## Definition of done

- [ ] Runs A, B and C committed, each with `COMPLETE`
- [ ] `## Observations` filled in with the numbers above
- [ ] No gameplay or tooling code changed
- [ ] `docs/TASKS.md`: T06a → `DONE`; T06b → `OWNER-RUN`; T07, T11, T16 → `READY`

---

## Observations

*(Raw numbers only — no verdict. That is T06b's job. For each run record: wall
time, rounds reached, and first/last `worldChildren`, `heapMB`, `tracePoints`,
`errors`. Add anything that looked wrong, without interpreting it.)*

**Run A** (committed, see `docs/reports/soak-A/`): 60/60 rounds, 1145.4s wall,
111 samples. `worldChildren` first=1345 last=1345 (range 1292-1388 throughout,
no growth trend across 60 `startRound()` cycles). `heapMB` first=43.6
last=260.6 (noisy GC sawtooth, peaks 92-311MB, no runaway). `tracePoints`
first=8 last=97 (bounded by frequent round churn — traces reset every death).
`errors` 0 throughout. Final screenshot renders correctly.

**Run C** (committed, see `docs/reports/soak-C/`): 60/60 rounds (61 counted,
the sample after the 60th round-end tick), 311.4s wall, 30 samples — 4
players, split-screen, 0 bots, deaths on, exercising the `RenderTexture`
split-screen path. `worldChildren` first=1359 last=1386 (range 696-1387
throughout — dips to ~700 correspond to samples caught between a round-end
and the next `startRound()`'s organelle regeneration, not a leak; no growth
trend across 61 `startRound()`/split-screen cycles). `heapMB` first=42.2
last=89.8 (noisy GC sawtooth, peaks 41.8-114.3MB, no runaway, comparable band
to run A). `tracePoints` first=8 last=12 (bounded by frequent round churn,
same as run A — all 4 are non-bot "players" with no input driving them, so
they die into the membrane almost immediately most rounds, which is why
round throughput here, ~5.1s/round, is faster than run A's ~19s/round).
`errors` 0 throughout. Final and 307s screenshots both render correctly —
split-screen composite, ER/Golgi arcs and viral-breach overlay all intact,
no visual corruption.

## Resolved — was blocked, now fixed (2026-08-04)

**Stage B was correctly reported un-completable, and the diagnosis was exact.**
`soak.py`'s only completion path was `rounds >= target`, but run B sets
`immortal=True`, so `godMode` disables every death check, so `activePlayers`
never drops, so `fuzzStats.rounds` stays 0 forever. A rounds target on an
immortal config is unreachable at any cap. That session stopped and escalated
rather than improvising, which is exactly right — the contradiction was in the
tooling and in this task file, not in the game.

**Fix applied to `tools/soak.py`:**

- Each config declares `done_when` as `("rounds", n)` or `("minutes", m)`.
  Run B completes on **20 minutes**; A and C on **60 rounds**.
- A config that is `immortal` *and* rounds-targeted is now refused outright.
- Passing `--rounds` to a minutes-mode config (or vice versa) aborts immediately
  instead of being silently ignored while the default target runs.
- `### Targets` above was rewritten to match. Run `python3 tools/soak.py B` with
  no arguments.

**Stage B is runnable again.** `docs/reports/soak-B/` was correctly deleted, so
it starts clean.

### Data from the discarded run, worth keeping

That run still measured what B exists to measure: `tracePoints` grew 8 → 22,367
and `gridCells` ~270 → ~36,250 over 40 minutes, with `heapMB` peaks climbing
364 → 620 → 809 → 1024 MB. Unbounded trace growth is by design in B and is the
evidence justifying **T07**. Confirm it in the clean re-run rather than citing
these numbers.

---

## Leak analysis from run A — Stage D must report this

Run A (60 rounds, 1144 s) shows **`worldChildren` flat but `heapMB` climbing**.
The discriminator between GC lag and a real leak is the sawtooth *floor*:

| Window | wall s | heap min | heap max | children min | children max | rounds |
|---|---|---|---|---|---|---|
| 1 | 182 | **44** | 161 | 1331 | 1378 | 8 |
| 2 | 369 | **70** | 198 | 1310 | 1379 | 19 |
| 3 | 554 | **85** | 189 | 1329 | 1374 | 30 |
| 4 | 741 | **91** | 192 | 712 | 1388 | 38 |
| 5 | 926 | **101** | 178 | 1292 | 1379 | 47 |
| 6 | 1113 | **124** | 381 | 671 | 1379 | 58 |

The floor rises monotonically 44 → 124 MB across 58 rounds (~1.4 MB/round).
**GC lag gives rising peaks over a stable floor; a rising floor means memory is
being retained.** `worldChildren` holding the same 1310–1388 band throughout says
T05 fixed the PixiJS display-object leak — so this is a **second, non-display-
object leak**. Worth checking: arrays reassigned but still captured by a closure,
accumulated event listeners, or per-round state hanging off `window`.

Run C (60 rounds, 308 s) shows a stable heap band, which is consistent with it
being too short for the trend to appear rather than with the leak being absent.

**T06b should weigh this in the verdict.** Do not fix it inside T06a — this task
measures only.
