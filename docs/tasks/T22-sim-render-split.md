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

- [x] Step 1 — vesicles split
- [x] Step 2 — infection split
- [ ] Step 3 — organelles split (sprite mirroring moved to draw)
- [ ] Step 4 — mitosis split (three state mutations moved out of the draw path)
- [ ] Step 5 — players/traces split
- [ ] Step 6 — `gameLoop` restructured into `stepSimulation` + `renderFrame`
- [ ] Step 7 — headless step loop exposed and benchmarked

Commit per step (`T22: <step>`), push, then decide whether there is budget for
the next. Leave T22 `READY` until every step is ticked.

---

## Findings

**Step 1 (vesicles split), landed 2026-08-10.** `updateVesicles(delta)` now
contains state only: both spawn blocks, the Gen 4+ well `gen4EstablishTime`
latch, and the per-vesicle loop (gravity pull, feed-meter consume + T57
transform trigger, membrane/organelle bounce, fusion + splice). A new
`drawVesicles()` does `dynamicLayer.clear()`, the Gen 4+ well rings/flash/
establish-pulse, then draws each surviving vesicle by `v.type` — same
reverse-index (`vesicles.length - 1` down to `0`) iteration as the old fused
loop, so on-screen z-stacking of overlapping vesicles is unchanged. No
`Math.random()` call was added, removed, or reordered relative to other
`gameLoop` update calls; the call site became `updateVesicles(delta);
drawVesicles();` in the same slot the single call used to occupy (mirroring
T51's `updateATP(); drawATP();` pattern already next to it).

Verified: static extraction of `updateVesicles`'s source shows zero
`PIXI`/`*Layer`/`.sprite`/`.visible` references (the mechanical check this
task exists to make possible). A non-immortal 30-game-second round (1 player +
3 bots, harness default) ran clean — 2/4 alive at 30.3s, 1 vesicle in flight,
console/page errors empty. A 15-game-second immortal run with
`window.setGeneration(4)` forced confirmed the harder path: the Gen 4+ well
rings, HUD "NUCLEUS" label and per-consume flash all rendered (screenshot),
and `nucleusFeed.value` rose from 0 to 12 with `gen4EstablishTime`/
`nucleusFeedFlashTime` both set, proving the consume branch (feed meter,
particle burst, T57 transform-trigger check) still fires correctly from
inside the split-out `updateVesicles`. `node --check` on the extracted
`<script>` body passed. `dist/` rebuilt (`--check` passes); `sw.js`
`CACHE_NAME` bumped v23→v24.

Not yet measured (belongs to step 7, not this step): headless speedup. No
headless stepper exists until `gameLoop` itself is restructured in step 6.

**Step 2 (infection/virus split), landed 2026-08-10.** `updateInfection(delta,
deltaSec)` now contains state only: the `none`→`warning` trigger, the
breach transition (particle spawn, `addShake`, `nextWarningTime`,
`state = 'none'`), the `textClearTime` clear, and the per-particle physics/
destroy loop. A new `drawInfection()` does `virusLayer.clear()`, the hexagon
warning glyph, then the per-particle virus-blob draw (`moveAngle` recomputed
from `vp.vx/vp.vy`, a pure read, instead of being stashed). One state field
was added, `infection.warningVisible` (set in `updateInfection`, read in
`drawInfection`) — needed because the original code drew the hexagon glyph
*before* checking whether this frame's breach flips `infection.state` from
`'warning'` back to `'none'`; if `drawInfection()` had instead tested
`infection.state === 'warning'` directly, the glyph would silently vanish
one frame early on every breach since `updateInfection()` (and its state
flip) now runs to completion before `drawInfection()` is called at all.
`warningVisible` is set to `true` on entry to the `'warning'` branch (mirroring
the original's draw-then-maybe-flip order) and `false` in the `else`, then
read as-is in `drawInfection()` — reproducing the exact old timing. Added to
both `infection = {...}` initializers (declaration and `startRound()` reset).
No `Math.random()` call was added, removed, or reordered. Call site is
`updateInfection(delta, deltaSec); drawInfection();` in the same `gameLoop`
slot, mirroring step 1's `updateVesicles(); drawVesicles();` pattern.

Verified: static extraction of `updateInfection`'s source shows zero
`PIXI`/`*Layer`/`.sprite`/`.visible` references; `drawInfection()` reviewed by
hand to confirm it only reads `infection.*` fields and never mutates them.
A targeted check forced `infection.nextWarningTime` to fire in ~1s (1 player +
3 bots immortal): mid-warning state showed `{state: 'warning', warningVisible:
true, particles: 0}` with the hexagon glyph screenshotted; 6s later, past the
5s breach window, showed `{state: 'none', warningVisible: false, particles:
25}` (25 of the 30 spawned particles survived contact with a lysosome —
expected, unchanged physics) with virus particles screenshotted mid-flight.
A separate normal (non-immortal) 30-game-second round with 1 player + 3 bots
ran clean: bot moved, traces grew to 931 points, human died to the membrane
as expected with nobody driving it, console/page errors empty in both checks.
`node --check` on the extracted `<script>` body passed. `dist/` rebuilt
(`--check` passes, confirmed clean over `file://` too); `sw.js` `CACHE_NAME`
bumped v24→v25.

Next: Step 3 — organelles split (sprite mirroring moved into `drawOrganelles()`).

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
