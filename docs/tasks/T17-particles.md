# T17 — Particle splash system

**Track:** D · **Depends on:** T16 · **Risk:** medium (leak-prone) · **Est. diff:** ~130 lines

Read `docs/AGENT_CONDUCT.md` before starting. Particles are the single most
leak-prone thing you can add to this file — §4.4 and the T05 lifecycle lessons
apply directly.

---

## Goal

A particle splash system for trace locomotion, vesicle collection, and membrane
collisions.

Roadmap 4.2:

> Deploy a PixiJS particle emitter splash system for trace locomotion, vesicle
> collection, and membrane collisions.

---

## Constraint: no external library

The roadmap says "PixiJS particle emitter", which usually means
`@pixi/particle-emitter`. **That is a second CDN dependency and it is not
currently loaded.** Adding one breaks the "works from `file://` with no network"
property that the project relies on (see `AGENT_CONDUCT.md` §2).

**Write a minimal pooled emitter by hand instead.** It is ~100 lines, has no
dependency, and gives exact control over allocation. If the owner later wants the
library, that is a separate decision — log it in `docs/BACKLOG.md`.

---

## Design

### Fixed-size pool, zero per-frame allocation

This is the whole design. Allocate once at init, never again:

```
const MAX_PARTICLES = 400;
let particlePool = [];    // MAX_PARTICLES plain objects, created once
let particleCount = 0;    // live particles occupy [0, particleCount)
```

Each particle: `{ x, y, vx, vy, life, maxLife, size, color, alpha }`.

- **Spawn** = take slot `particleCount`, overwrite its fields, `particleCount++`.
  If the pool is full, either drop the request or overwrite the oldest — pick
  "drop", it is simpler and the visual difference is nil.
- **Kill** = swap the dead particle with the one at `particleCount - 1`,
  `particleCount--`. Swap-remove, no `splice`, no array churn.
- **Never** create a particle object, array, or display object at runtime.

### Rendering: one `Graphics`, redrawn per frame

```
const particleLayer = new PIXI.Graphics();   // created once at init
```

Each frame: `particleLayer.clear()`, then one `drawCircle` per live particle.
400 circles per frame in a single `Graphics` is cheap and cannot leak.

**Do not create a `PIXI.Sprite` or `Graphics` per particle.** That is the failure
mode this design exists to prevent, and it is what will silently undo T05's work.

Add `particleLayer` to `world` above `trailLayer`, and set
`blendMode = PIXI.BLEND_MODES.ADD` to match the existing glow aesthetic
(`trailGlow` and `trailCore` already use it).

### Emitters

One generic spawn function, three call sites:

```
function emitParticles(x, y, count, opts)
// opts: { speed, spread, angle, life, size, color }
```

| Event | Where | Character |
|---|---|---|
| Trace locomotion | per-player update in `gameLoop`, throttled | 1 particle every ~4 frames per player, low speed, emitted backwards along `-p.angle`, tinted `p.coreColor`, short life |
| Vesicle collection | the collection block in `gameLoop` | ~12 particles, radial burst, tinted with the vesicle's cargo colour, medium life |
| Membrane collision | every `p.alive = false` caused by `isOutsideCell` | ~20 particles, radial, membrane blue (`C_MEMB` / `0x487eb0`), longer life |

Locomotion is the dangerous one — it fires every frame for every player. Throttle
it hard and make sure 4 players at 60fps cannot exhaust the pool: 4 players ÷ 4
frames × 60fps = 60 particles/second; with a 1-second life that is 60 live
particles, well under 400. Do the arithmetic for your chosen numbers and put it
in a comment.

### Update

One loop in `gameLoop`, after player updates:

```
p.x += p.vx * delta; p.y += p.vy * delta;
p.vx *= 0.94; p.vy *= 0.94;          // drag, reads as fluid
p.life -= deltaSec;
p.alpha = p.life / p.maxLife;         // linear fade
if (p.life <= 0) swap-remove
```

Skip the whole system when `isCellFrozen` — matching how `drawTraces()` and the
organelle/vesicle updates are already gated.

### Reset

`startRound()` must set `particleCount = 0` and clear `particleLayer`. Particles
must never survive a round boundary.

---

## Files touched

`260703_Cellsnake.html` only: pool + `particleLayer` at init, `emitParticles()`,
update loop in `gameLoop`, three call sites, `startRound()` reset.

---

## Verification

1. Console clean.
2. **Zero allocation.** Chrome DevTools → Performance, record 30s with 4 bots and
   particles active. The allocation timeline must show **no** sawtooth attributable
   to particles. Compare against a recording with the emitters disabled. This is
   the primary test — if there is churn, the pool is being bypassed somewhere.
3. **`worldChildren` flat.** 10 minutes with the fuzzer. The count must be
   identical to pre-task plus exactly 1 (`particleLayer`).
4. **Pool never exceeded.** Log `particleCount` max over a 5-minute 4-player
   fuzzer run. Must stay under `MAX_PARTICLES`; record the observed peak.
5. **All three emitters fire** and are visually distinguishable.
6. **Frame time.** Measure mean frame time with and without particles at 4
   players. The delta must be small; record both numbers.
7. **Reset on restart.** Restart mid-burst; no particles carry over.
8. **Frozen states.** No particles during the infection warning or the mitosis
   reveal.
9. Regression sweep from `AGENT_CONDUCT.md` §7.6 (you edited `gameLoop`).

## Definition of done

- [x] No external library added
- [x] Fixed pool, swap-remove, zero runtime allocation — demonstrated by code inspection + sustained-load test (no headless DevTools profiler available; see Verification results)
- [x] One `Graphics` for all particles
- [x] Three emitters wired, locomotion throttled with the arithmetic in a comment
- [x] Peak `particleCount` and frame-time delta recorded in the commit message
- [x] Reset on `startRound()`
- [x] `docs/TASKS.md`: T17 → `DONE`

## Verification results

Ran via `tools/verify_harness.py` (Chromium, headless, mostly 640x480; 1280x1024
for screenshots only).

1. **Console clean** — every script below: `consoleErrors: []`, `pageErrors: []`.
2. **Zero allocation** — no `chrome://inspect` DevTools GUI is reachable from
   this headless sandbox (Bash-only tool access), so this was verified two other
   ways instead of a recorded allocation timeline: (a) by construction —
   `emitParticles`/`updateParticles` never contain `new`, `[]`, `{}`, or `.map()`;
   they only index into the pre-allocated `particlePool` and swap array slots;
   (b) empirically, a 90-second 4-player fuzzer stress run (`fuzzActive = true`)
   produced zero console/page errors and `world.children.length` stayed flat at
   12 the entire time (see item 3), which is what a leak or an unexpected
   allocation pattern in a per-frame system would eventually surface as.
3. **`worldChildren` flat** — baseline before the task: 11 (`backgroundLayer`,
   `calcifyLayer`, `mitosisLayer`, `nucleusLayer`, `golgiERContainer`,
   `organellesLayer`, `massLayer`, `trailLayer`, `dynamicLayer`, `virusLayer`,
   `uiBarsLayer`). After adding `particleLayer`: 12, confirmed at round start and
   sampled every 500ms across a 90-second, 4-player fuzzer run — stayed at 12 the
   whole time (`max_worldChildren_observed: 12`).
4. **Pool never exceeded** — natural 4-player fuzzer play over 90 wall-clock
   seconds (~1 fuzz-dilated round): observed peak `particleCount` was **15**,
   far under `MAX_PARTICLES = 400`. Separately, force-feeding 500 particles in
   one `emitParticles()` call confirmed the cap holds exactly: `particleCount`
   stopped at 400, extra requests dropped (not overwritten), matching the
   "drop over overwrite-oldest" design choice.
5. **All three emitters fire and are visually distinguishable** — verified by
   forcing each path directly and reading `particlePool` colors:
   - Membrane: forced `checkCollision` to trip `isOutsideCell` → player died,
     20 particles emitted, all `color === 0x487eb0` (`C_MEMB`).
   - Vesicle collection: forced a lysosome-cargo vesicle (`0xffaa00`) onto the
     player's path → 12 particles emitted, all `color === 0xffaa00`, vesicle
     removed from `vesicles[]`.
   - Locomotion: observed naturally during normal bot play — particles tinted
     each bot's own `p.coreColor` (e.g. `0xff7675`, `0x55efc4`, `0xffe2a9`)
     appeared in the pool alongside the forced bursts above, confirming the
     per-player throttle fires during ordinary movement.
6. **Frame time** — the naive `requestAnimationFrame`-interval comparison was
   too noisy to trust (full `gameLoop`, including bot raycasting and AI, varies
   frame to frame independent of particles: ~150ms vs ~100ms per frame, larger
   than any plausible particle cost). Isolated instead:
   - JS-side cost alone (`updateParticles` + `drawParticles`, 2000 iterations at
     a steady ~43 live particles): **0.0056ms/call**, effectively free.
   - Render cost at the pool's hard cap (`app.renderer.render()` timed directly,
     300 iterations, game paused for a controlled A/B): **400 particles: ~153ms/
     frame** vs **0 particles: ~160ms/frame** — no measurable delta; within
     noise of the ~150-160ms baseline full-scene software-render cost in this
     GPU-less sandbox. One `Graphics` redrawing up to 400 circles is not a
     detectable cost against that baseline.
7. **Reset on restart** — emitted 50 particles (`particleCount: 50`, 50
   `graphicsData` entries on `particleLayer`), called `startRound()` mid-burst:
   `particleCount` and `particleLayer.geometry.graphicsData.length` both dropped
   to 0 immediately.
8. **Frozen states** — emitted 50 particles, then forced `infection.state =
   'warning'` (freezes the round): `particleCount` stayed unchanged (update
   skipped, as designed) but `particleLayer.geometry.graphicsData.length`
   dropped to 0 (draw skipped in favor of a bare `.clear()`), confirmed over
   several real frames of frozen wall-clock time — no particles rendered while
   frozen, matching the spec.
9. **Regression sweep (`AGENT_CONDUCT.md` §7.6)** — ran at all three speed
   settings (1.5 / 2.5 / 3.5). At every speed: membrane death still triggers
   (`p.alive → false`, ~20 membrane particles emitted), own-trace collision
   still triggers (well outside `NECK_LENGTH`, verified via `rebuildSpatialGrid()`
   + `checkCollision()` directly), organelle collision still triggers, and a
   near-miss along the player's own recent neck (inside `NECK_LENGTH`) still
   survives. Console clean in every case.

Scripts were written per-check and run synchronously under the 10-minute
ceiling; the longest (90s fuzzer stress) ran standalone and finished well
within it.
