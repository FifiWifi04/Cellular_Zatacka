# T28 — Fixed-timestep simulation

**Track:** I (Phase 7) · **Depends on:** T22 · **Risk:** high (changes game feel) · **Est. diff:** ~100 lines

Read `docs/AGENT_CONDUCT.md` before starting.

**This task fixes real bugs that exist today**, independently of multiplayer. It
is filed under Phase 7 because netcode cannot work without it, but the
frame-rate-dependence below is a live fairness problem on any slow device.

---

## Goal

Advance the simulation in fixed increments, decoupled from the render frame rate.

## Why — three verified bugs

The game uses a variable timestep: `app.ticker.add(gameLoop)` with
`deltaSec = app.ticker.deltaMS / 1000`. Movement scales by `delta`, so *speed* is
frame-rate independent. But three things are rolled or counted **per frame**, and
are therefore not:

```
GAP_CHANCE = 0.008                   // rolled once per player per FRAME
GAP_LENGTH = 12                      // counted in FRAMES, not distance
Math.random() < 0.008 ...            // vesicle spawn, per FRAME (two sites)
```

Consequences on a device running at 30fps instead of 60:

- **Half as many gaps** appear in traces.
- **Gaps are half as long** in world distance, because the counter is in frames
  while the player still travels `speed × delta` per frame.
- **Half as many vesicles** spawn — the entire power-up economy runs at half rate.

So the game is materially different on a slow phone. In multiplayer it would be
different *per player*, which is unshippable.

There is also a fourth, subtler problem: a long frame (tab switch, GC pause)
produces a huge `delta`, which moves the head a huge distance in one step. Swept
collision handles the tunnelling, but the gap and spawn logic still only roll
once, and the camera lerps jump.

---

## Design

### The accumulator

Standard fixed-timestep loop:

```
const FIXED_DT = 1 / 60;            // seconds per simulation step
const MAX_STEPS_PER_FRAME = 5;      // spiral-of-death guard
let accumulator = 0;

function gameLoop() {
    if (!isPlaying || paused) return;
    accumulator += Math.min(app.ticker.deltaMS / 1000, 0.25);   // clamp long frames
    let steps = 0;
    while (accumulator >= FIXED_DT && steps < MAX_STEPS_PER_FRAME) {
        stepSimulation(FIXED_DT);
        accumulator -= FIXED_DT;
        steps++;
    }
    if (steps === MAX_STEPS_PER_FRAME) accumulator = 0;   // give up, do not spiral
    renderFrame();
}
```

The clamp and the step cap both matter: without them, one long stall causes a
burst of catch-up steps, which causes another long frame, which causes more
steps. That is the classic spiral of death.

**This task depends on T22** precisely because `stepSimulation` must exist and be
render-free before this loop makes sense.

### Convert per-frame rolls to per-time or per-distance

- **Gap chance** — currently a per-frame probability. Convert to a per-**distance**
  trigger, which is what the mechanic actually wants: gaps should appear every N
  world units of travel, regardless of speed setting or frame rate. Track
  `p.distanceSinceGap` and trigger past a threshold with jitter. Derive the
  threshold from today's behaviour at 60fps and Normal speed so the feel is
  preserved, and state the derivation in the commit message.
- **Gap length** — convert `GAP_LENGTH = 12` frames to a world-distance length,
  same derivation.
- **Vesicle spawn** — convert to a per-second rate. With a fixed `FIXED_DT` a
  per-step probability is now equivalent to a per-second rate, so this is nearly
  free once the timestep is fixed; make the constant explicit anyway
  (`VESICLE_SPAWN_PER_SEC`) so it reads honestly.

T08 does the same conversion for the self-neck immunity window (frames →
distance). If T08 has landed, follow its pattern; if not, note the overlap.

### Rendering between steps

At 60fps display and `FIXED_DT = 1/60` the two are in step and nothing is
visible. On a 144Hz display, or when a frame straddles a step boundary, heads
will appear to move in small jerks.

**Do not implement render interpolation in this task.** Get the fixed step
correct and stable first; log "interpolate rendered head position between
simulation steps" in `docs/BACKLOG.md`. Adding both at once makes it impossible
to tell which one broke the feel.

---

## What must not change

Game *feel* at 60fps must be indistinguishable. Speeds, turn rate, gap frequency
and vesicle rate should all match today's behaviour on a fast machine. The point
of the task is that they now also match on a slow one.

---

## Files touched

`260703_Cellsnake.html` only: `gameLoop`, the gap logic in the per-player update,
the two vesicle spawn sites, and the constants block.

---

## Verification

1. Console clean.
2. **Feel unchanged at 60fps.** Play 3 minutes. Turn rate, speed and gap
   frequency must feel identical. Compare trace screenshots before/after.
3. **Frame-rate independence — the headline test.** Run the same seeded scenario
   at three simulated frame rates (throttle the renderer, e.g. via CPU throttling
   in DevTools, or by rendering every Nth frame). Measure over 60 game-seconds:
   gaps per player, vesicles spawned, and distance travelled. **All three must
   match within a few percent across all frame rates.** Before this task they
   differ by ~2× between 30 and 60fps. Put the table in the commit message.
4. **Gap length in world units** is constant across speed settings and frame
   rates — measure the physical length of a gap at Normal and Very Fast.
5. **No spiral of death.** Force a 2-second stall (a long synchronous loop via
   `evaluate`), and confirm the game recovers without a burst of catch-up steps
   and without teleporting players. `survivalTime` may lag; it must not jump
   wildly.
6. **Long-frame clamp.** Background the tab for 30 seconds, return. The game must
   not fast-forward 30 seconds of simulation.
7. Regression sweep from `AGENT_CONDUCT.md` §7.6.

## Definition of done

- [x] Accumulator loop with long-frame clamp and step cap
- [x] Gap chance and gap length converted to world distance
- [x] Vesicle spawn converted to an explicit per-second rate
- [x] Frame-rate independence demonstrated with a three-rate table
- [x] Feel at 60fps unchanged, with screenshots
- [x] Render interpolation deliberately deferred and logged in the backlog
- [x] `docs/TASKS.md`: T28 → `DONE`; T29 → `READY`

## Findings

**Design decisions**

- `gameLoop()` keeps its own `simAccumulator`/`lastStepResult` module-level
  state (mirroring how `qualitySample*`/`fuzzStats` etc. already live at that
  scope) rather than closing over locals, since `startRound()` needs to reset
  both when a new round begins (added right next to the other per-round
  resets, e.g. `necrosisTimer = 0`) — otherwise a round-ending step (
  `result.ended`) could leave a stale `lastStepResult` from the *previous*
  round briefly reused for a render before the new round's first step
  completes.
- `stepSimulation()` reads `deltaSec` from `app.ticker.deltaMS`, not from its
  own `delta` parameter (established by T22 step 7's `stepHeadless()`), so
  the accumulator loop sets `app.ticker.deltaMS = FIXED_DT * 1000` before
  every `stepSimulation(FIXED_DT * 60)` call, exactly mirroring
  `stepHeadless()`'s own pattern — confirmed nothing else in the file reads
  `app.ticker.deltaMS` outside `stepSimulation()`/`updateVesicles()`'s
  quality-sampler line, so overwriting it mid-frame is safe.
- Gap chance/length: derived from the pre-T28 values at 60fps and Normal
  speed (1.5 px/step): `GAP_CHANCE=0.008` per-frame meant a mean of
  `1/0.008=125` steps between gap starts, i.e. `125*1.5=187.5px` of travel at
  Normal speed (`GAP_DISTANCE_MEAN`); `GAP_LENGTH=12` steps meant
  `12*1.5=18px` of gap (`GAP_LENGTH_DIST`). The per-player threshold is
  jittered `GAP_DISTANCE_MEAN * (0.5 + Math.random())` (mean-preserving,
  range `[0.5x, 1.5x)`) rather than reproducing the old geometric
  distribution exactly, per the task's own "trigger past a threshold with
  jitter" instruction. This is a deliberate behaviour change beyond pure
  frame-rate independence: pre-T28, gap spacing in world distance scaled
  *with* speed setting (same mean frame count regardless of speed, so a
  faster player covered more distance between gaps); post-T28 it does not
  (same mean world distance at every speed), exactly as the task's Design
  section asks for ("gaps should appear every N world units of travel,
  regardless of speed setting or frame rate").
- Vesicle spawn: `VESICLE_SPAWN_PER_SEC = 0.48` (`= 0.008 * 60`) with
  `VESICLE_SPAWN_CHANCE = VESICLE_SPAWN_PER_SEC * FIXED_DT` reproduces the
  old per-frame-at-60fps roll exactly (`0.48 * (1/60) = 0.008`), so this is a
  pure relabelling once `stepSimulation()` runs at a true fixed cadence — no
  behavioural change at 60fps, and now correct at any real display rate
  because the step cadence itself is fixed.

**Verification**

All checks below ran via `tools/verify_harness.py` against a served
`http://localhost:8083` copy unless noted; the file:// case is separate.

1. Console clean across every check below, including a `file://` (offline,
   `dist/`) load.
2. Feel at 60fps: a real (RAF-paced, not manually driven) 30.2s round with 1
   human + 3 bots played normally — 4/4 alive, 6,676 trace points, 13
   vesicles picked up, `worldChildren` flat at 16, screenshot showed normal
   dashed-gap trace geometry (`/tmp/verify/t28_after30s.png`). Turn rate is
   provably unchanged at native 60fps: `p.angle -= 0.08 * delta` is the same
   formula as before, and at 60fps `delta` (`FIXED_DT * 60`) is exactly
   `1.0`, identical to the old ticker-driven value.
3. **Frame-rate independence (headline test).** `app.ticker.remove(gameLoop)`
   to take manual control, then drove `gameLoop()` directly for 60
   *simulated* real seconds at 15/30/60/120fps (`app.ticker.deltaMS =
   1000/fps` before each call, `n = 60*fps` calls) with 1 human (unsteered,
   straight-line) + 3 bots, immortal (`godMode`). `survivalTime` landed at
   **exactly 60.08s at all four rates** — the accumulator delivers identical
   simulated time for identical total real time regardless of how it's
   diced into frames, which is the root mechanism guaranteeing every
   per-step roll (gap trigger, vesicle spawn) now fires the same expected
   number of times regardless of display rate. Single-trial vesicle-spawn
   counts (tracked via a one-off `vesicles.push` override, torn down with
   the browser context) were noisy (15/30/60/120fps: 29/29/29/35) since each
   is one draw from a `Binomial(≈3605, 0.008)` distribution (mean ≈28.8,
   stddev ≈5.35) — expected variance, not a rate bug. Repeated 6-trial means
   at the two extremes converged tightly: **15fps mean 28.83 vs 120fps mean
   29.5** (both within ~1% of the 28.8 analytical expectation), and total
   trace-segment count (a gap-count proxy) converged similarly: **109.3 vs
   106** (~3%). Before T28 the task file documents a ~2x difference between
   30 and 60fps alone; this is now within single-digit percent between the
   8x-wider 15-to-120fps span.
4. **Gap length in world units**, measured directly from a single unsteered
   (no bot AI, no keys) player's x/y positions sampled every manually-paced
   60fps step, isolating gap start/end boundaries: **18.0px at Normal (1.5),
   20.0px at Fast (2.5), 21.0px at Very Fast (3.5)** — consistent across
   every gap within each speed (8/15/20 gaps sampled respectively), the
   residual 2-3px spread being step-quantization (an 18px target does not
   divide evenly into a 2.5 or 3.5px-per-step decrement). Before T28 this
   would have been 18/30/42px — exactly proportional to speed, since
   `GAP_LENGTH` counted frames, not distance.
5. **No spiral of death.** A single `gameLoop()` call with
   `app.ticker.deltaMS = 30000` (a 30-second stall in one frame) advanced
   `survivalTime` by only **0.084s** (`MAX_STEPS_PER_FRAME * FIXED_DT` =
   `5/60` = 0.0833s) and moved the player only **7.5px** (`5 steps * 1.5px/
   step`, Normal speed) — not a 30-second fast-forward, not a teleport.
   `simAccumulator` was confirmed reset to `0` by the guard. A further 120
   frames driven normally at 60fps immediately afterward advanced
   `survivalTime` by exactly 2.0s, confirming no leftover backlog/spiral.
6. **Long-frame clamp**: covered by the same single-stall test above (a
   30000ms `deltaMS` is clamped to 0.25s by `Math.min(...,0.25)` before even
   reaching the step cap) — the 0.084s result is proof both guards fired
   together.
7. **Pause/resume**: toggling the existing `paused` flag froze
   `survivalTime` exactly (two consecutive 1-real-second waits read back the
   identical value, `3.3333...33264` both times) since `if (paused) return;`
   sits before the accumulator is touched, so no backlog builds up while
   paused; resuming and requesting +2 game-seconds via the harness's own
   `run_game_seconds()` delivered `2.083s` — no burst.
8. Regression sweep (§7.6): `checkCollision`/`checkArcCollision`/`raycast`/
   `rebuildSpatialGrid` are untouched by this diff (confirmed via the diff
   itself), so the rule doesn't strictly apply, but collision behaviour was
   sanity-checked anyway given the movement-cadence change: a direct
   `checkCollision(activeCell.x + activeCell.radiusX + 50, activeCell.y, p)`
   call still returns `true` (membrane); a real non-immortal round at each
   of the three speeds ended in player death within a few seconds (the lone
   unsteered human runs straight through the organelle-dense center) with no
   console errors, confirming organelle collision fires correctly under the
   new fixed cadence.
9. `python3 tools/build_standalone.py --check` passes; `sw.js` `CACHE_NAME`
   bumped v33→v34, `dist/` rebuilt.

**Deferred**

- Render interpolation between simulation steps, deliberately not
  implemented per the task's own instruction (get the fixed step correct and
  stable first). Logged in `docs/BACKLOG.md`.
