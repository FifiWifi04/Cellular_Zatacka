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

- [ ] No external library added
- [ ] Fixed pool, swap-remove, zero runtime allocation — demonstrated in DevTools
- [ ] One `Graphics` for all particles
- [ ] Three emitters wired, locomotion throttled with the arithmetic in a comment
- [ ] Peak `particleCount` and frame-time delta recorded in the commit message
- [ ] Reset on `startRound()`
- [ ] `docs/TASKS.md`: T17 → `DONE`
