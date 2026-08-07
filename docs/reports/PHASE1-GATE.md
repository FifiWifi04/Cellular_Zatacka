# Phase 1 Gate — **PASS**

**Verdict: PASS.** Phase 1 is mathematically stable and performance-tested.
Signed off 2026-08-07 by the owner (T06b).

---

## Setup

| | |
|---|---|
| Driver | `tools/soak.py` (rounds- or duration-targeted, flushes per sample, writes `COMPLETE` only on success) |
| Harness | `tools/verify_harness.py`, headless Chromium, 640×480 |
| Machine | Sandboxed container, **no GPU** — software WebGL, ~0.38× real time |
| Runs | A (60→453 rounds, deaths on), B (20 min, immortal), C (61 rounds, split-screen) |

**Important: the three runs were taken at different commits.** Run A was
re-measured by T06c at `8762fcf`; runs B and C date from `42fff14` and `db4e9c5`
respectively, both of which **predate T07** (`bacaf5b`, the per-player trace cap).
That distinction drives the whole leak analysis below.

## Results

### Heap sawtooth **floor** per window — the leak test

The floor is the level memory returns to after collection. A rising *peak* over a
stable floor is GC lag; a rising *floor* is retention.

| Run | Commit | Floors across 6 windows (MB) | Trend |
|---|---|---|---|
| **A (original)** | `30ec41a` | 44 → 70 → 85 → 91 → 101 → **124** | **rising** |
| **A (re-measured)** | `8762fcf` | 41.7 · 47.3 · 42.3 · 43.2 · 48.2 · **42.5** | **flat** |
| B | `42fff14` *(pre-T07)* | 42.5 · 103.2 · 122.6 · 235.8 · 238.4 · **241.2** | rising |
| C | `db4e9c5` *(pre-T07)* | 41.8 · 53.6 · 56.9 · 46.8 · 46.2 · **44.1** | flat |

### Other series

| Run | Rounds | Wall | Samples | `worldChildren` min/max | `errors` |
|---|---|---|---|---|---|
| A | 453 | 1063 s | 104 | 684 / 1393 | **0** |
| B | 0 *(immortal by design)* | 1203 s | 116 | 1303 / 1356 | **0** |
| C | 61 | 311 s | 30 | 698 / 1387 | **0** |

## Leak analysis

**The retention found at the original measurement is gone.**

Run A originally showed the heap floor climbing 44 → 124 MB over 60 rounds
(≈1.4 MB/round) while `worldChildren` stayed flat — the signature of memory
retained outside the PixiJS display list. T06c re-measured at `8762fcf` over a
**longer and much harder** run (453 rounds vs 60) and the floor is flat:
41.7–48.2 MB with no trend.

**Cause: T07's per-player trace cap.** Unbounded trace point arrays were the
retained memory. No additional code change was required — T06c's Step 0
re-measurement resolved the question before any investigation began.

**Run B's rising floor is not a counter-example.** Run B is the immortal
configuration where nothing dies and traces grow without bound *by design*, and
it was measured at `42fff14`, **before** T07 existed. Its 42 → 241 MB rise is
exactly the unbounded trace growth T07 was written to fix. It is stale evidence,
not contradicting evidence.

**`worldChildren` held flat across every run**, confirming T05's display-object
teardown is correct and stayed correct through T07–T17.

## Errors

**Zero.** No console errors, no page errors, no `undefined` crashes across all
three runs — 514 rounds and roughly 43 minutes of continuous fuzzing combined.

## Performance

- **Bot raycast** (T01): DDA traversal with stamp-based dedup replaced fixed-step
  sampling; the per-step `Set`+array allocation (~90/bot/frame) is gone.
- **Trace rendering** (T25): per-frame `drawTraces()` cost was rising ~5.5× from
  15 s to 120 s of game time; it is now flat within noise. RenderTexture pair is
  1550×1350 at scale 0.5, ≈16 MB.
- **Trace growth** (T07): bounded per player, which is what fixed the leak.

## Roadmap sign-off

**1.1 — Heuristic AI bot.** Satisfied. Three-ray sensor (forward/left/right)
detecting the elliptical membrane, player traces, microtubules, ER/Golgi walls,
organelles, virus particles and vesicles. Hazard and reward are separate
channels; steering weights are normalized and proportional.

> Note: the roadmap says the bot should "simulate virtual key presses". The
> implementation steers `bot.angle` directly at the same `MAX_TURN` rate a human
> gets. Functionally equivalent and mechanically simpler. Recorded as a
> deliberate deviation, not a gap.

**1.2 — Fuzzer.** Satisfied. `fuzzActive` dilates time 4×, forces mitosis and
infection continuously, tops vesicles and virus particles to their caps, flips
player and camera modes, and restarts rounds instantly. `window.fuzzStats`
reports rounds, errors and live counts; global `error` and `unhandledrejection`
traps are installed. Crucially, T04 separated `godMode` from `fuzzActive`, so the
fuzzer now runs **with** death checks enabled — before that it could not have
detected a collision bug at all.

## Findings and follow-ups

1. **Retention — RESOLVED** by T07. No action.
2. **Runs B and C are stale** (both predate T07). Not gating: run A is the
   meaningful series for retention, and it was re-measured. Re-run B and C at the
   current build when convenient, for a clean matched set.
3. **No GPU in the measurement environment.** All timings are software-rendered
   and are useful only as relative comparisons. Absolute frame-time claims about
   real hardware are not supported by this data.

## What this does not cover

The gate covers stability and memory. It says nothing about **gameplay quality**
— the owner's 2026-08-07 playtest found eleven separate issues, written up as
T33–T42. Those are correctness and design work, not gate failures.
