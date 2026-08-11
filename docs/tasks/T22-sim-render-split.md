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
- [x] Step 3 — organelles split (sprite mirroring moved to draw)
- [x] Step 4 — mitosis split (three state mutations moved out of the draw path)
- [x] Step 5 — players/traces split
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

**Step 3 (organelles split), landed 2026-08-10.** `updateDriftingOrganelles(delta)`
now contains state only: drift/velocity, the outside-cell and failsafe clamps,
the pair-resolution/fusion loop, and `o.rotation += o.rotSpeed * delta`
(unconditional now, not gated on `o.sprite` -- gating a state mutation on a
display-object reference would itself violate the "zero display-object
references" rule this task exists to enforce; `o.sprite` is set atomically
with every `organelles.push()` and cleared only via `destroyNecroticOrganelle()`,
which splices the organelle out of `organelles` in the same call, so no
organelle ever sits in the array with a missing sprite -- the guard was always
true in practice and removing it changes nothing observable). A new
`drawOrganelles()` does the exact old tail unchanged: `sprite.x/y` mirror,
`sprite.rotation` mirror for non-necrotic organelles, and the necrotic
freeze-flicker alpha formula (a pure function of `survivalTime`/`o.freezeTime`).
Call site became `updateDriftingOrganelles(delta); drawOrganelles();` in the
same `gameLoop` slot, mirroring steps 1-2's pattern. No `Math.random()` call
was added, removed, or reordered.

Verified: `awk` extraction of `updateDriftingOrganelles`'s source shows zero
`PIXI`/`Layer`/`.sprite`/`.visible` references (the only hit is a comment in
the following function). A 30-game-second immortal round (1 player + 3 bots)
found `spriteMismatches: 0` across all 25 organelles (an exact per-frame
`sprite.x === o.x`, `sprite.y === o.y`, and for non-necrotic ones
`sprite.rotation === o.rotation` check) -- proving the split didn't desync the
mirror even by a frame. Forcing Gen 2 and running 13.6s produced one necrotic
organelle whose sprite alpha had settled at the resting `NECROSIS_ALPHA`
(0.75) with x/y still exactly mirrored, confirming the freeze-flicker path
still fires correctly from `drawOrganelles()`. A real (non-immortal)
30.5-game-second round with 1 player + 3 bots played normally (662 trace
points, 2/4 alive, the unpiloted human died to the membrane as expected,
2 bots survived) with console clean. `file://` load (offline, in `dist/`)
ran 10.5 game-seconds clean too. `node --check` on the extracted `<script>`
body passed. Exact-position parity against a pre-change baseline was not
attempted: `Math.random()` is unseeded, so two separate browser process runs
of *even identical code* never produce identical organelle trajectories --
the same limitation steps 1-2 hit, worked around the same way (structural/
sanity checks instead of byte-for-byte state diff). `dist/` rebuilt (`--check`
passes); `sw.js` `CACHE_NAME` bumped v25→v26.

**Step 4 (mitosis split), landed 2026-08-10.** Moved exactly the three state
mutations named by this task from `drawMitosisVisuals()` into `updateMitosis()`:
the `crossedCenter` computation (pure function of `mitosis.direction`,
`activeCell`, `mitosis.cellB` and `sweepProgress` — no display-object reads),
then on the frame it first goes true, `addShake(0.7, 0.6)`, `spawnVesicles(...,
15, 'membrane', 0x6c5ce7)`, and `centralHitboxes = []`, `mitosis.nucleusDestroyed
= true`. `drawMitosisVisuals()` now only does `nucleusLayer.visible =
!mitosis.nucleusDestroyed; golgiERContainer.visible = !mitosis.nucleusDestroyed;`
— a pure read-and-mirror.

The one-shot gate for the trigger used to be `if (nucleusLayer.visible)` (a
display-object read, forbidden in `updateMitosis()`); it is now `if
(crossedCenter && !mitosis.nucleusDestroyed)`. That required also finding
where the old gate got re-armed: `generateMap()` unconditionally resets
`nucleusLayer.visible = true` (line ~1833), and the mitosis snap calls
`generateMap(true)` — so every new cell started life with `nucleusLayer.visible`
true again, letting the *next* mitosis event destroy the *next* nucleus.
`mitosis.nucleusDestroyed`, by contrast, was never reset anywhere. Copying only
the three named mutations without also mirroring that implicit re-arm would
have silently broken every mitosis event after the first (nucleus never
destroyed again, `centralHitboxes` never cleared, no vesicle burst) — so one
line, `mitosis.nucleusDestroyed = false;`, was added immediately after the
`generateMap(true);` call at the snap, matching exactly where the old code's
implicit reset happened.

Verified: `awk`-extracted the new block from `updateMitosis()` — zero
`PIXI`/`Layer`/`.sprite`/`.visible` references outside of comments. `node
--check` on the extracted `<script>` body passed. Two scripted direct-state
checks (matching prior steps' "direct function call" methodology, since the
real 120s-per-event timing doesn't fit a session's wall budget): (1) parked
mitosis mid-event just below the crossing threshold, let ~0.5 game-seconds
elapse — `mitosis.nucleusDestroyed` flipped true, `nucleusLayer.visible`/
`golgiERContainer.visible` both went false, a sentinel `centralHitboxes` was
cleared to `[]`, 15 new `0x6c5ce7` vesicles appeared, and `shakeDecayTime` rose
from 0 to 0.6 (confirming `addShake` fired) — all matching the pre-split
behaviour exactly. (2) Forced the SNAP directly (`devMode` set so the
snap's pre-existing devMode-gated, not godMode-gated, player-kill check didn't
wipe the roster — a known unrelated bug already in `docs/BACKLOG.md`):
`mitosis.nucleusDestroyed` correctly reset to `false` post-snap
(`nucleusVisible`/`golgiVisible` back to `true`, generation incremented 1→2),
then a second forced crossing on the new cell re-triggered the destruction
(`nucleusDestroyed` → `true` again, `centralHitboxesLen` → `0`) — proving the
reset fix reproduces the old multi-event behaviour, not just the first event.
Screenshots confirm visual parity: nucleus/Golgi/ER fully rendered before the
forced crossing, gone immediately after. A real (non-immortal) 30.2-game-second
round with 1 player + 3 bots played normally (966 trace points, 3/4 alive,
console clean, screenshot looks normal). An 8.2-game-second `file://` load
(offline, source file with `vendor/` alongside it) also ran clean. `dist/`
rebuilt (`--check` passes); `sw.js` `CACHE_NAME` bumped v26→v27.

Not moved (out of scope for this step, matches the task's own three-item
list): `mitosis.currentWidth`, still computed inside `drawMitosisVisuals()`
even though it's read by `checkArcCollision`-adjacent physics code
(`isCellFrozen`/gap checks around line 2172/5645) — a pre-existing §4.4
violation that predates this task and wasn't part of the three named
mutations; noted in `docs/BACKLOG.md`. Also unmoved: the large PIXI-heavy
block in `updateMitosis()`'s own event-trigger section (Cell B background,
cytosol particles, organelle sprites) — this already existed in
`updateMitosis()` before this task and is not part of the "three state
mutations" this step was scoped to.

**Step 5 (players/traces split), landed 2026-08-11.** The old fused
`gameLoop`, `players.forEach((p, pi) => {...})` — bot AI/input, all seven
swept collision checks (trace/organelle, microtubule, malignant mass, nucleus
chaser, viral swarm), vesicle and ATP granule pickup, gap/ghost trace
management, the trace-point append, and the mitosis death-ring sweep — moved
verbatim into a new `updatePlayers(delta, deltaSec, isCellFrozen)`. The only
thing pulled *out* of that body (not just relocated) was the four per-player
uiBarsLayer status bars (ghost/hunter/golgi/speed) and the standalone
`uiBarsLayer.clear()` call that used to precede the loop, plus the T51 global
ATP-pause bar that used to follow it — all three now live in a new
`drawPlayerBars()`.

The per-player bars needed more than a cut-and-paste: in the original, each
bar was drawn *mid-iteration*, using that player's `p.effects.*`/`p.x`/`p.y`
values from immediately after that frame's countdown decrement but *before*
that same frame's collision/pickup logic could still change them (a blue/red/
mitochondria vesicle pickup mutates `p.effects.*`, movement mutates `p.x/y`,
both later in the same original iteration). Splitting into two full passes
(`updatePlayers()` for every player, then `drawPlayerBars()` for every player)
would have made every bar reflect *this* frame's post-pickup values instead —
a real, observable behaviour change, not just a code move. Fixed by
snapshotting the values the bars need (`p.barX/barY`,
`p.barGhostTimer/HunterTimer/GolgiTimer/SpeedTimer/SpeedLevel`) onto the
player object at the exact point in `updatePlayers()` the old bar-draw block
used to run (right after the decrement, before the `isCellFrozen` early
return) — plain property writes on the existing player object, not a
per-frame allocation. `drawPlayerBars()` reads only those snapshot fields.
The global ATP bar needed no such snapshot: the original drew it once, after
the *entire* forEach had finished for every player, so it always reflected
the full frame's pickups already — reading `calcifyPauseTimer` in
`drawPlayerBars()` (called after `updatePlayers()` returns) is the same value
at the same point in the frame, unchanged. New fields
(`barX`/`barY`/`barGhostTimer`/`barHunterTimer`/`barGolgiTimer`/
`barSpeedTimer`/`barSpeedLevel`) were added to the player object's own
initializer next to the other per-round-reset fields (`particleTick`,
`assemblyTick`) for consistency, though nothing depends on their defaults —
`updatePlayers()` always runs before `drawPlayerBars()` within the same
`gameLoop` tick. Call site is `updatePlayers(delta, deltaSec, isCellFrozen);
drawPlayerBars();` in the exact slot the old forEach + bar code occupied. No
`Math.random()` call was added, removed, or reordered relative to other
`gameLoop` calls.

Not PIXI-free: `updatePlayers()` still calls `destroyNecroticOrganelle()`/
`breakClusterMember()` from section 0.9 (attack-mode necrotic-organelle
break), which touch `organellesLayer`/`.sprite` internally. That coupling
predates this split (T13/T38/T50, same spot in the old fused loop) and
untangling it is a separate, larger change — filed to `docs/BACKLOG.md` for
whoever audits `stepSimulation()`'s zero-display-object-references invariant
in step 6/7.

Verified: brace-matched extraction of `updatePlayers()`'s source (4550-4883)
shows zero `PIXI`/`Layer`/`.sprite`/`.visible` references; `drawPlayerBars()`
(4892-4946) reviewed by hand and confirmed to only read `p.bar*`,
`calcifyPauseTimer`, `activeCell`, `survivalTime` and never mutate them.
`node --check` on the extracted `<script>` body passed. A real 30.2-game-second
round (1 player + 3 bots, harness default) played normally — 3/4 alive (the
unpiloted human died to the membrane as expected), 942 trace points, console
clean, screenshot looks normal. A regression sweep confirmed all three swept
death paths still fire via direct state-forcing at Normal speed (membrane,
self-trace via a manually-placed neck segment past `isOwnNeck`'s distance
immunity, and organelle), plus 15-game-second real rounds at all three speed
settings (Normal/Fast/Very Fast) with 3/4 alive and console clean at each.
Vesicle pickup verified end-to-end with a real `spawnVesicles()`-created
mitochondria vesicle: `vesicles.length` 1→0 and `p.effects.speedTimer` 0→9.9
on contact, with `p.barSpeedTimer` correctly still 0 on the pickup frame's own
bar (matching the old pre-pickup timing) and mirroring 9.9 the *next* frame —
proving the snapshot ordering fix actually works, not just that it compiles.
ATP granule pickup verified the same way (`calcifyPauseTimer` 0→3.9 on
contact). Forced every effects timer nonzero on a parked player and
screenshotted the resulting stacked bars and the separately-forced ATP bar —
both render at the expected position. `dist/` rebuilt (`--check` passes);
`sw.js` `CACHE_NAME` bumped v27→v28.

Not moved (pre-existing, out of scope): the "DEATH RING SHATTER LOGIC" block
immediately before where the old `players.forEach` started (organelle/Golgi-
arc destruction during a mitosis sweep, including a `drawArcs()` call) is
about organelles/arcs, not players, and was left untouched in `gameLoop`.

Next: Step 6 — `gameLoop` restructured into `stepSimulation` + `renderFrame`.

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
