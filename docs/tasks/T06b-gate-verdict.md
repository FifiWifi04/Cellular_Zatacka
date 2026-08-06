# T06b — Phase 1 gate verdict

**Track:** A · **Depends on:** T06a · **Risk:** none (no code at all) · **Est. diff:** one report

**👤 OWNER-RUN — a scheduled agent session must SKIP this task** and take the
next `READY` one instead. This is a judgement about whether your project's
Phase 1 is finished. A machine should not make it.

---

## Goal

Read the data T06a collected, decide **PASS or FAIL** on Phase 1, and write the
sign-off.

## Why this is separate from T06a

T06a is measurement; this is judgement. Splitting them means the routine can
produce the evidence and keep working on T07, T11 and T16 without waiting for
you, while the decision that actually gates the project stays with you.

The cost of that split, stated honestly: a few tasks may land before you deliver
the verdict. Each is individually verified, so the exposure is small — but if you
return a FAIL, check whether anything built since T06a needs revisiting.

---

## What you need

- `docs/reports/soak-A/`, `soak-B/`, `soak-C/` — each with a `COMPLETE` marker.
  **If a marker is missing, that run is truncated — do not analyse it.** Send it
  back to T06a.
- `docs/tasks/T06a-soak-measurement.md` → `## Observations`
- Commit messages from T01 (raycast timings) and T05 (before/after teardown
  numbers).

---

## How to read the data

Open each `soak.csv` and look at these series against `wall_s`:

| Series | Healthy | Unhealthy |
|---|---|---|
| `heapMB` | Sawtooth around a stable mean — GC reclaiming | A staircase that never returns to its floor = leak |
| `worldChildren` | **Flat across rounds** | Any sustained upward trend = display objects surviving `startRound()`; T05 missed a site |
| `tracePoints`, `gridCells` | Grow within a round, reset between (runs A, C) | In run B they grow without bound by design — record the rate, that is T07's input |
| `errors` | **0** | Anything above 0 blocks the gate outright |
| `alive` | Cycles as rounds turn over | Stuck at a constant = rounds are not actually restarting |

`worldChildren` is the leak canary — it counts display objects recursively under
`world`. Baseline measured on the current build during driver development was
~1,350 and flat. A number climbing round over round is the failure this whole
gate exists to catch.

---

## Write the report

Create `docs/reports/PHASE1-GATE.md`:

1. **Verdict** — PASS or FAIL, in the first line. No hedging.
2. **Setup** — commit SHA, browser version, viewport, each run's config, wall time.
3. **Results table** — the series above at start / 25% / 50% / 75% / end per run.
4. **Leak analysis** — an explicit statement on `worldChildren` and `heapMB`
   trajectory per run, with numbers.
5. **Error log** — every console/page error captured, or "none".
6. **Performance** — raycast timing from T01, grid rebuild cost vs. trace count
   from run B, any frame-time drift.
7. **Findings** — each issue numbered, with a proposed task ID. If run B shows
   the grid rebuild becoming a hotspot, say so and point at T07.
8. **Sign-off** — which bullets of roadmap 1.1 and 1.2 are now demonstrably
   satisfied, quoted from `Development_plan.md`.

---

## Definition of done

- [ ] All three runs had `COMPLETE` markers before you analysed them
- [ ] `docs/reports/PHASE1-GATE.md` written, verdict in the first line
- [ ] Every claim in it backed by a number from a CSV
- [ ] `docs/TASKS.md`: T06b → `DONE`
- [ ] No code changed

## Follow-up already staged

The owner reviewed the data on 2026-08-04 and accepted a **soft FAIL** on the
memory question: **[T06c](T06c-heap-leak-hunt.md)** is written and `READY`,
ahead of everything else on the board. You do not need to create it.

What is still yours: write `docs/reports/PHASE1-GATE.md` recording the verdict
and the numbers behind it, then set T06b `DONE`. T06c reports back into it.

One thing to weigh when you write it: all of Phase 3 and most of Phase 4 (T07,
T11–T17) landed *after* the measurement and before the verdict — that is the
window the T06a/T06b split deliberately created. Each of those tasks was
individually verified and `worldChildren` stayed flat throughout, so the
exposure looks small, but T06c's re-measurement on the current build is what
actually settles it.

## If the verdict is FAIL

1. Create a follow-up task file per issue under `docs/tasks/`.
2. Put them on the board as `READY`, **ahead of everything else**.
3. Set T07, T11 and T16 back to `BLOCKED` on those new tasks.
4. Review anything that landed between T06a finishing and now — that is the
   window the split created.

The gate exists to be honest about, not to be passed.
