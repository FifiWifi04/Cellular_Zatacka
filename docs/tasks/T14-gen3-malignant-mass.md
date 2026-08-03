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

- [ ] Blocks live in `spatialGrid`; sensor and physics use the same data
- [ ] Swept collision only
- [ ] Attack-mode shatter with cooldown; self-mode death
- [ ] Growth capped; placement validated
- [ ] One persistent `Graphics` for the whole mass
- [ ] Bot demonstrably avoids the mass
- [ ] Fragment-disconnection behaviour documented in this file
- [ ] `docs/TASKS.md`: T14 → `DONE`
