# T22 — Separate simulation from rendering

**Track:** G · **Depends on:** T06a · **Risk:** high (touches everything) · **Est. diff:** ~250 lines moved, few added

Read `docs/AGENT_CONDUCT.md` before starting. This is the largest structural task
on the board. It changes no behaviour — if the game plays differently afterward,
something went wrong.

---

## Goal

Make it possible to advance the game state **without drawing anything**, by
splitting every function that currently simulates-and-draws into an `updateX()`
that owns state and a `drawX()` that only reads it.

## Why — this pays for itself three times

1. **Multiplayer (Phase 7) is impossible without it.** A host must run the
   simulation headlessly; today there is no way to step the game without a
   renderer attached.
2. **Testing gets dramatically faster.** T06a's soaks run at ~0.38× real time
   because every frame rasterises. A headless step loop removes that ceiling
   entirely, which is the difference between a 40-minute soak and a 2-minute one.
3. **Mobile (Phase 6) needs the freedom** to render at a different cadence from
   the simulation.

## The problem, concretely

Simulation and rendering are fused. `updateVesicles()` is the clearest case — it
calls `dynamicLayer.clear()` and then, in the same pass, moves vesicles, checks
collection, *and* issues draw calls:

```
dynamicLayer.clear();
...
dynamicLayer.beginFill(v.color, 0.8);
dynamicLayer.drawCircle(v.x, v.y, v.radius);
```

The same pattern appears in `updateInfection()` (`virusLayer.clear()`),
`updateMitosis()` / `drawMitosisVisuals()`, and `gameLoop` itself.

---

## Design

### The target shape

```
function stepSimulation(dt) {     // pure state. No PIXI calls whatsoever.
    rebuildSpatialGrid();
    updatePlayers(dt);
    updateDriftingOrganelles(dt);
    updateVesicles(dt);
    updateInfection(dt);
    updateMitosis(dt);
}

function renderFrame() {          // pure reads. Never mutates game state.
    drawTraces();
    drawOrganelles();
    drawVesicles();
    drawInfection();
    drawMitosisVisuals();
    drawHud();
    updateCamera();
}

function gameLoop(delta) {        // the PIXI ticker entry point
    if (!isPlaying) return;
    stepSimulation(deltaSec);
    renderFrame();
}
```

### The rule that makes it verifiable

**`stepSimulation` and everything it calls must contain zero references to
`PIXI`, to any `*Layer`, to `.sprite`, or to any display object.** That is
mechanically checkable — see Verification 2. If you cannot remove a draw call
from an update function, the state it needs is missing; add the state.

### Doing it safely — one system per commit

Do **not** attempt this in one pass. Split it system by system, in this order,
verifying after each:

1. **Vesicles** — the clearest case, and self-contained. `updateVesicles()` keeps
   the motion, spawn and collection logic; a new `drawVesicles()` reads
   `vesicles[]` and draws. Move nothing else.
2. **Infection / virus** — same shape, `virusLayer`.
3. **Organelles** — `updateDriftingOrganelles()` already ends with a clean
   "sprite mirrors state" block (`o.sprite.x = o.x`). That mirroring is
   *rendering*: move it into `drawOrganelles()`.
4. **Mitosis** — hardest, because `drawMitosisVisuals()` currently *mutates*
   state: it clears `centralHitboxes`, sets `mitosis.nucleusDestroyed`, and calls
   `spawnVesicles()`. **All three are simulation** and must move into
   `updateMitosis()`. Read T02's commit before touching this; it is the site of
   a bug that was fixed there.
5. **Players / traces** — the trace append is simulation; `drawTraces()` is
   already pure. Mostly just moving the append out of the draw path if it is
   there.
6. **`gameLoop`** — finally, restructure into the two calls above.

> Each of steps 1–5 is a legitimate standalone commit. If session budget runs
> out, stop between steps, not inside one. Use the `## Progress` checklist.

### What must NOT change

- No gameplay constant, no timing, no random call **order** (order matters for
  Phase 7 and for reproducibility — keep the same sequence of `Math.random()`
  calls per frame).
- Not a fixed timestep. That is T28. Keep passing the existing variable `delta`
  through, unchanged, or you will conflate two large changes.
- No renaming beyond what the split requires.

---

## Progress

- [ ] Step 1 — vesicles split
- [ ] Step 2 — infection split
- [ ] Step 3 — organelles split (sprite mirroring moved to draw)
- [ ] Step 4 — mitosis split (three state mutations moved out of the draw path)
- [ ] Step 5 — players/traces split
- [ ] Step 6 — `gameLoop` restructured into `stepSimulation` + `renderFrame`
- [ ] Step 7 — headless step loop exposed and benchmarked

Commit per step (`T22: <step>`), push, then decide whether there is budget for
the next. Leave T22 `READY` until every step is ticked.

---

## Step 7 — the payoff

Expose a headless stepper so tests and (later) a host can drive the game without
a renderer:

```
window.stepHeadless = function (seconds, dt) {
    dt = dt || 1/60;
    for (let t = 0; t < seconds; t += dt) stepSimulation(dt);
};
```

Then add `run_headless_seconds()` to `tools/verify_harness.py` alongside
`run_game_seconds()`, and benchmark: how many game-seconds per wall-second does
`stepHeadless` achieve versus the ~0.38× of the rendered loop? Put both numbers
in the commit message. This is the number that decides whether T06a's soaks get
faster.

---

## Files touched

`260703_Cellsnake.html` (extensive but mostly moves), `tools/verify_harness.py`
(one new method in step 7).

---

## Verification

1. Console clean after every step.
2. **The mechanical check.** Extract the source of `stepSimulation` and every
   function it calls, and assert it contains no `PIXI`, no `Layer`, no `.sprite`,
   no `.visible`. Automate it in your verification script — this is the invariant
   the whole task exists to establish.
3. **Behaviour is identical.** Before starting, record a baseline: 60 game-seconds
   with 1 human + 3 bots immortal, logging `tracePoints`, `organelles`,
   `vesicles`, and every player's final `x/y/angle`. After each step, re-run and
   compare. Small floating-point drift is acceptable; a changed trace-point count
   or a bot dying where it did not before is not.
4. **Visual parity.** Screenshot the same scene before and after each step.
5. **Headless works** (step 7): `stepHeadless(10)` advances `survivalTime` by ~10
   and produces trace points, with nothing rendered.
6. **Headless speedup measured** and reported.
7. Regression sweep from `AGENT_CONDUCT.md` §7.6.

## Definition of done

- [ ] `stepSimulation()` provably free of display-object references
- [ ] `renderFrame()` provably free of state mutation
- [ ] Mitosis's three state mutations moved out of the draw path
- [ ] Behaviour parity demonstrated against a recorded baseline
- [ ] `window.stepHeadless` exposed; speedup measured and reported
- [ ] `docs/TASKS.md`: T22 → `DONE`; T28 → `READY`

## Rollback

Each step is its own commit, so a bad step reverts alone. If parity cannot be
demonstrated for a step, revert that step and record why under `## Blocked`.
