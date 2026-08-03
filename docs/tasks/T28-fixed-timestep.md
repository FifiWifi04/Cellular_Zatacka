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

- [ ] Accumulator loop with long-frame clamp and step cap
- [ ] Gap chance and gap length converted to world distance
- [ ] Vesicle spawn converted to an explicit per-second rate
- [ ] Frame-rate independence demonstrated with a three-rate table
- [ ] Feel at 60fps unchanged, with screenshots
- [ ] Render interpolation deliberately deferred and logged in the backlog
- [ ] `docs/TASKS.md`: T28 → `DONE`; T29 → `READY`
