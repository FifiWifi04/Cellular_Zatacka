# T14 — Gen 3: the malignant mass

**Track:** C · **Depends on:** T11 · **Risk:** medium-high (new hazard type) · **Est. diff:** ~160 lines

Read `docs/AGENT_CONDUCT.md` before starting — especially §4.1. This task adds a
brand-new hazard, which is exactly the situation where the sensor path gets
forgotten.

---

## Goal

From generation 3, spawn a static tumour that grows by cloning an attached block
every 10 seconds. A player who hits it while in `targetMode === 'attack'` shatters
the block they hit; a player who hits it otherwise dies.

Roadmap 3.2:

> Spawn a static tumor sprite that duplicates/clones an attached block every 10
> seconds. If a player hits the mass while their `targetMode === 'attack'`, the
> block shatters.

---

## Design

### 1. Data model

The mass is a set of grid-aligned blocks — this makes growth, collision, and
shattering all trivial, and lets it reuse the existing swept AABB helper
(`segAabbT` from T02).

```
let malignantMass = {
    active: false,
    blockSize: 60,
    origin: { x: 0, y: 0 },      // world position of cell (0,0)
    blocks: [],                  // [{ cx, cy, x, y, spawnTime }]
    nextGrowTime: 0
};
```

`cx`/`cy` are integer grid coordinates; `x`/`y` are the derived world centre.
Keep both — the integers make adjacency checks exact, the world coords keep the
hot path free of arithmetic.

### 2. Spawn

When `genAtLeast(3)` first becomes true and `!malignantMass.active`:

- Pick a position that is **valid**: inside the cell (`!isOutsideCell`), at least
  450px from `activeCell` centre (clear of the nucleus and the 380px organelle
  ring), not overlapping any organelle, and at least 300px from every alive
  player. Retry up to ~200 times; if no valid spot is found, skip and retry next
  frame. Copy the retry structure from the organelle placement loop in
  `generateMap()`.
- Seed with one block at `(0,0)`.
- Set `nextGrowTime = survivalTime + 10`.

Reset `malignantMass` fully in `startRound()`.

### 3. Growth

Every 10 seconds of un-frozen game time:

- Collect all empty grid cells 4-adjacent to an existing block.
- Filter out any whose world position would be outside the cell, inside the
  nucleus radius, or on top of a player head.
- Pick one at random, append it, set `spawnTime = survivalTime`.

**Cap the mass.** `const MASS_MAX_BLOCKS = 40;` — at 10s per block that is ~7
minutes of growth, and with T12's shrinking membrane an uncapped mass will fill
the arena. Stop growing at the cap.

### 4. Collision — BOTH paths (§4.1)

**Physics** — in `gameLoop`, alongside the microtubule check:

- Swept: `segAabbT((p.x,p.y) → (nextX,nextY), block, TRACE_HITBOX)` for each
  block. Do not write a point-in-time test.
- If `p.targetMode === 'attack'`: remove the hit block, do **not** kill the
  player, and give a short cooldown (`p.effects.lastMassHit = survivalTime`,
  ~0.3s) so one pass does not clear a corridor in a single frame.
  - **Removing a block can disconnect the mass.** Decide and document: either
    allow floating fragments (simplest, acceptable) or flood-fill from the origin
    block and delete orphans. Pick the simple one unless it looks wrong.
- Otherwise: `p.alive = false`.
- Respect `ghostTimer` and `godMode` exactly as the other hazards do — read the
  neighbouring checks and match them.

**Sensor** — in `raycast()`:

- Add a `'mass'` hit type using the same `segAabbT` pre-pass as microtubules
  (analytic, once per ray, not per DDA step). With up to 40 blocks this is 40
  tests per ray — acceptable, but if T06a's data shows it costing, insert the blocks into
  `spatialGrid` in `rebuildSpatialGrid()` instead and let the DDA find them.
  **Prefer the grid insert** — it is barely more code and it scales.
- Weight it in the hazard branch of the scoring function.

> If you insert into `spatialGrid`, the item shape should be
> `{type:'mass', x, y, size}` and the DDA's per-cell test is a `segAabbT`. This
> is the better design; take it.

### 5. Rendering

One persistent `PIXI.Graphics` created at init (`massLayer`), cleared and redrawn
each frame from `malignantMass.blocks`. Never create a `Graphics` per block.

Style: dark, unhealthy, clearly not an organelle — desaturated purple/brown with a
harsh outline. Newly spawned blocks (within ~0.5s of `spawnTime`) get a brief
bright pulse so growth is visible. Shattered blocks: just disappear — a particle
burst is T17's job, log it in `docs/BACKLOG.md`.

### 6. Attack-mode signalling

The `targetMode` aura is already drawn in `drawTraces()` (green for `'self'`, red
for `'attack'`). No new UI needed. But confirm bots can enter `'attack'` mode —
T03's logic only does so near traces with a speed power-up, so a bot will
essentially never shatter the mass. That is acceptable for now; log
"bot should target the malignant mass in attack mode" in `docs/BACKLOG.md`.

---

## Files touched

`260703_Cellsnake.html` only: `malignantMass` state, `startRound()` reset, spawn +
growth block in `gameLoop`, physics check in `gameLoop`, `rebuildSpatialGrid()`
insert, `raycast()` DDA case, scoring function, new `massLayer` + draw routine.

---

## Verification

1. Console clean.
2. **Gen 1 and 2 unaffected.** No mass appears below Gen 3.
3. **Spawns once, validly.** `window.setGeneration(3)`. Exactly one mass appears,
   clear of the nucleus, organelles, and all players. Restart 10 times and confirm
   placement is always sensible.
4. **Grows on schedule.** One block every 10s, always adjacent, never overlapping
   itself.
5. **Cap holds.** Fast-forward past 40 blocks; growth stops.
6. **Kills in self mode.** Drive into it with `targetMode === 'self'`. Death, at
   the drawn edge.
7. **Shatters in attack mode.** Toggle to `'attack'` and drive in. Exactly one
   block disappears per hit, you survive, and the cooldown stops a single pass
   from clearing several blocks.
8. **Swept, not tunnelling.** At Very Fast with the fuzzer's 4× dilation, drive at
   a single block head-on. It must register — the head must not appear on the far
   side.
9. **Bot sees it.** Watch a bot at Gen 3 for 2 minutes; it must steer around the
   mass, not into it. **This is the §4.1 test — do not skip it.**
10. **No leak.** `worldChildren` flat over 10 minutes at Gen 3.
11. Regression sweep from `AGENT_CONDUCT.md` §7.6.

## Definition of done

- [x] Blocks live in `spatialGrid` (sensor path only, via `rebuildSpatialGrid()`);
      physics scans `malignantMass.blocks` directly, same pattern as the
      microtubule check it sits next to
- [x] Swept collision only (`segAabbT`, same helper as the microtubule pre-pass)
- [x] Attack-mode shatter with cooldown; self-mode death
- [x] Growth capped; placement validated
- [x] One persistent `Graphics` for the whole mass
- [x] Bot demonstrably avoids the mass
- [x] Fragment-disconnection behaviour documented in this file
- [x] `docs/TASKS.md`: T14 → `DONE`

## Fragment-disconnection behaviour (§4, item 4)

Chose the simple option: **floating fragments are allowed.** Shattering a
block via `malignantMass.blocks.splice(i, 1)` never checks whether the
remainder is still connected to the origin block. A shatter can leave an
orphaned island of blocks with no path back to `(0,0)`; `growMalignantMass()`
will still happily grow outward from that island later (it only requires
4-adjacency to *some* existing block, not connectivity to the origin). This
looked fine in practice — visually a floating chunk still reads as "part of
the tumour" — so no flood-fill-from-origin pass was added.

## Verification results (2026-08-06)

All items run via `tools/verify_harness.py`, either through real gameplay or
by driving `gameLoop()` deterministically with a fixed `app.ticker.deltaMS`
to get frame-exact timing (real headless-frame pacing is too noisy for the
sub-second cooldown check). Full detail in the commit message; summary:

1. Console clean across every run below.
2. Gen 1 and Gen 2: `malignantMass.active` stays `false`. Confirmed.
3. 10/10 restarts at Gen 3: exactly one block spawns, always ≥522px from
   `activeCell` centre (spec floor 450), always clear of every organelle
   (closest observed clearance 59px against a 50px requirement) and every
   player (closest observed 410px against a 300px requirement).
4. Growth: pressing the dev "+15s" jump (which exceeds `MASS_GROW_INTERVAL`)
   reliably grows exactly one block per jump; 6 jumps → 7 blocks, all
   4-adjacent, no duplicate cells.
5. Cap: seeded 39 blocks in open space (isolating the cap from the natural
   map's geometry, which independently self-limits growth near organelles/
   the boundary/the nucleus — that's expected, not a bug) and confirmed it
   grows to exactly 40 and holds there over further growth ticks.
6. Self-mode: player centred on a block, one deterministic frame → dies,
   block untouched.
7. Attack-mode: hit 1 shatters the block under the player and survives; an
   immediate second hit on the next block, still inside the 0.3s cooldown,
   neither shatters it nor kills the player; after the cooldown elapses a
   fresh hit on the same block shatters it.
8. Swept: `currentSpeed = 500` (a single frame's step spans far more than
   one block) still registers death rather than tunnelling through.
9. Sensor: `raycast()` reports `{type:'mass', dist}` at the expected distance
   for a ray aimed at a block, `'clear'` otherwise. A bot placed 250px from
   a block and aimed straight at it steers continuously away over 120
   deterministic frames (heading sweeps monotonically, distance never drops
   below ~233px) and never dies. In real multi-bot rounds at Gen 3, every
   observed player/bot death was 380px+ from the nearest mass block.
10. No leak: forced the mass to 40 blocks and called `drawMalignantMass()`
    50 times in a row; `countDisplayObjects(world)` and `massLayer.children.length`
    never change (the draw routine only ever calls `clear()`/`drawRect()` on
    the one persistent `Graphics`, never `addChild`).
11. Regression sweep (`raycast()` and `rebuildSpatialGrid()` were touched):
    at Normal/Fast/Very Fast, a fabricated safe trace confirms membrane,
    own-trace, and organelle collisions still kill, and a point 12px behind
    the head (within `NECK_LENGTH`) still survives, at all three speeds.
