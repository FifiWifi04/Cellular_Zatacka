# T15 — Gen 4: angiogenesis gravity well

**Track:** C · **Depends on:** T11 · **Risk:** low · **Est. diff:** ~50 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

From generation 4, a gravity well at the cell centre exerts a constant inward pull
on all spawned vesicles.

Roadmap 3.3:

> Center a gravity well that exerts a constant, inward pull vector on all spawned
> vesicles.

---

## Why this is the easy one

The roadmap is explicit that the pull applies to **vesicles only** — not players,
not organelles. Vesicles are already fully owned by `updateVesicles()`, they are
not lethal, and nothing else reads their velocity. So this is a contained change
with no collision implications and no sensor implications.

**Resist scope creep.** Pulling players would be a much bigger change (it fights
the steering model and the bot's assumptions) and it is not what the roadmap says.
If it seems like a good idea, log it in `docs/BACKLOG.md`.

---

## Prerequisites

Read `updateVesicles()` in full and `spawnVesicles()`. Establish:

- Do vesicles have velocity fields (`vx`/`vy`), or are they static once placed?
  The mitosis burst spawns 15 vesicles "flying outward", so some motion model
  exists — find it and reuse it. Write what you find under `## Findings` below
  **before** implementing.
- What is the vesicle lifetime / despawn rule?
- What happens when a vesicle reaches the cell centre — is the nucleus core lethal
  to vesicles, or will they pile up at the centre?

The last question decides the whole design. Answer it first.

---

## Design

### 1. The pull

In `updateVesicles()`, gated on `genAtLeast(4)`:

```
const GRAVITY_ACCEL = 12;   // px/s² toward the centre
const GRAVITY_MAX_V = 60;   // px/s terminal speed, so vesicles stay collectable
```

For each vesicle: compute the unit vector toward `activeCell.x/y`, add
`GRAVITY_ACCEL * deltaSec` to its velocity along that vector, clamp total speed to
`GRAVITY_MAX_V`, integrate position.

The terminal-velocity clamp is what keeps the mechanic fun rather than punishing —
without it, vesicles near the centre accelerate to uncollectable speeds.

`updateVesicles(delta)` currently takes frame-`delta`, not seconds. Check which
one it receives from `gameLoop` and use the matching unit consistently. Getting
this wrong makes the pull frame-rate dependent — a real bug, not a cosmetic one.

### 2. The centre problem

Vesicles that reach the middle land inside the 130px lethal nucleus core, where no
player can ever collect them. Handle it explicitly — pick one and document it:

- **Preferred:** when a vesicle comes within `~150px` of the centre, despawn it
  (it has been "consumed by the vasculature"). Cheap, self-cleaning, and it keeps
  the vesicle count churning rather than accumulating a dead pile.
- Alternative: park them on a 150px ring, orbiting. More interesting, more code,
  and it creates a permanent bait-ring right next to the lethal nucleus — which
  may actually be the more fun design. Decide by playing it.

Either way, vesicles must never accumulate unbounded at the centre. Verify the
count stays under the existing 25 cap.

### 3. Mitosis interaction

During a mitosis event there are two cells (`activeCell` and `mitosis.cellB`).
Pull each vesicle toward its **nearest** cell centre — `updateDriftingOrganelles()`
already contains exactly this `nearestCell` pattern; copy it rather than inventing
a new one.

### 4. Visual

A subtle indicator that the well is active. Cheapest good option: draw 2–3 faint
concentric rings around the centre in the existing `dynamicLayer` (which is
already cleared and redrawn each frame in `updateVesicles`), slowly rotating or
pulsing. **No new layer, no new display objects, no particle system** — T17 owns
particles.

Gate the visual on `genAtLeast(4)` too, so Gen 1–3 look identical to today.

---

## Files touched

`260703_Cellsnake.html` only: `updateVesicles()` — pull, clamp, centre handling,
and the ring visual.

---

## Verification

1. Console clean.
2. **Gen 1–3 unaffected.** Play a Gen 3 round; vesicle motion must be identical
   to before and no rings must be drawn.
3. **Gen 4 pull is visible.** `window.setGeneration(4)`. Vesicles drift inward
   steadily and smoothly.
4. **Frame-rate independence.** Run at Normal speed, then with the fuzzer's 4×
   dilation. The pull must scale with time, not with frame count. If a vesicle
   takes 8s to reach the centre normally, it must take ~2s at 4×.
5. **Still collectable.** Collect at least 5 moving vesicles by hand. The terminal
   velocity must make this comfortable, not twitchy.
6. **No pile-up.** Watch 5 minutes at Gen 4. Vesicle count must stay bounded and
   nothing may accumulate at the centre.
7. **Mitosis.** Trigger mitosis at Gen 4. Vesicles near Cell B must be pulled to
   Cell B, not across the bridge to Cell A.
8. **Nothing else moves.** Confirm players and organelles are completely
   unaffected — this is the scope-creep check.
9. **No leak.** `worldChildren` flat over 10 minutes at Gen 4.

## Definition of done

- [x] `## Findings` filled in (vesicle motion model, lifetime, centre behaviour)
- [x] Pull applies to vesicles only
- [x] Time-based, not frame-based; verified at 4× dilation
- [x] Terminal velocity clamp keeps vesicles collectable
- [x] Centre behaviour chosen, documented, and bounded
- [x] Nearest-cell logic during mitosis, reusing the organelle pattern
- [x] Visual gated on Gen 4, drawn into an existing layer
- [x] `docs/TASKS.md`: T15 → `DONE`

---

## Findings

- **Motion model:** vesicles already carry `vx`/`vy` (px per `delta`-tick) set at
  spawn (`spawnVesicles()`: random angle, speed 2.0-4.0; the Golgi drip in
  `updateVesicles()`: speed 0.8) and integrated each frame with
  `v.x += v.vx * delta; v.y += v.vy * delta;`. `delta` is PIXI's ticker
  `deltaTime`, normalized so 1.0 == a 60fps frame; `deltaSec` (`app.ticker.deltaMS
  / 1000`, computed once in `gameLoop`) is real elapsed seconds. Both are scaled
  by the same 4x factor under the fuzzer, and `delta` always equals `60 *
  deltaSec` frame-for-frame, so `delta` alone is already frame-rate/time-scale
  correct — the existing `vx`/`vy` values are effectively "px per 1/60s", i.e.
  real px/s divided by 60. `GRAVITY_ACCEL`/`GRAVITY_MAX_V` are specified in real
  px/s(²), so they are pre-divided by 60 once into module-level constants and
  then combined with `delta` exactly like the existing `v.rotation += 0.02 *
  delta;` line, instead of adding a second delta-flavor parameter to
  `updateVesicles()`.
- **Lifetime:** no age/despawn timer. A vesicle lives until it "fuses" (matching
  organelle type, or any membrane-type vesicle touching the outer wall) and is
  `splice()`d out. Concurrent count is capped at 25 by the spawn gates
  (`vesicles.length < 25`), not by any per-vesicle expiry.
- **Cell centre:** `isInsideNucleus()` (130px core) is lethal to players but is
  never consulted by `updateVesicles()` — nothing currently stops a vesicle
  drifting into/through the nucleus, and since players die on approach, a
  vesicle parked there would be permanently uncollectable. Chose the
  **preferred** despawn option from the design section: consume any vesicle
  within 150px of its nearest cell centre.
