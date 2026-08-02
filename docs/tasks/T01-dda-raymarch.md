# T01 — DDA ray-march in `raycast()`

**Track:** A (Phase 1 gate) · **Depends on:** — · **Risk:** medium · **Est. diff:** ~70 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Replace the fixed-step sampling loop inside `raycast()` with a grid-walking DDA
(digital differential analyser) traversal, and eliminate the per-step `Set` and
array allocations. Bot behaviour must not change in any way a player can notice.

## Why

`raycast()` currently advances in 12px steps to a 350px range (~30 steps) and
calls `spatialGrid.queryRange()` at every step. `queryRange()` allocates a fresh
`new Set()` **and** a fresh results array on every call. With 3 rays per bot that
is roughly **90 allocations per bot per frame**, ~5,400/second at 60fps with one
bot. This is the single measurable performance regression in Phase 1 and it must
be gone before the phase gate.

DDA visits each grid cell along the ray **exactly once**, in order, so the ray
also stops at the true nearest hit rather than the nearest 12px sample — a
correctness improvement for free.

---

## Prerequisites

Read these three functions in full first:

- `class SpatialGrid` — note `cellSize = 128`, `this.cells` is a `Map` keyed
  `` `${cx},${cy}` ``.
- `rebuildSpatialGrid()` — note what item shapes go in: `{type:'trace', x1,y1,x2,y2,
  playerId, s, i, segLength}`, `{type:'organelle', raw}`, `{type:'vesicle', raw}`,
  `{type:'virus', raw}`.
- `raycast(startX, startY, angle, maxDist, casterId)` — the function you are
  rewriting.

---

## Behaviour contract — what must NOT change

The function keeps its exact signature and return shape:

```
raycast(startX, startY, angle, maxDist, casterId = null)
  -> { dist: <number>, type: <string>, raw?: <object> }
```

`type` is one of `'boundary'`, `'nucleus'`, `'trace'`, `'organelle'`,
`'virus'`, `'vesicle'`, `'clear'`. `raw` is present only for `'vesicle'`.

All existing hit semantics are preserved verbatim:

- `isOutsideCell(rx, ry)` → `'boundary'`
- distance to `activeCell` centre `< 130 + TRACE_HITBOX` → `'nucleus'`
- the mitosis sweep-ring test (all four `mitosis.direction` cases) → `'boundary'`
- self-trace immunity: skip the caster's own last segment when
  `item.i >= item.segLength - 16`
- mitochondria: un-rotate by `-org.rotation`, 5-segment quadratic spine,
  `halfL = org.radius * 1.6 / 2`, `halfW = org.radius * 0.9 / 2`, radius
  `halfW + TRACE_HITBOX`
- lysosomes: circle, `org.radius + TRACE_HITBOX`
- virus: `vp.radius * 1.4 + TRACE_HITBOX`
- vesicle: `v.radius + TRACE_WIDTH + 6`, returns `raw: v`
- no hit → `{ dist: maxDist, type: 'clear' }`

**Do not change any of these constants or thresholds in this task.** T03 changes
the semantics; T01 changes only how we get there.

---

## Implementation plan

### Step 1 — Add a non-allocating query to `SpatialGrid`

Add two things to the class, leaving `queryRange()` untouched (it is still used by
`checkCollision()`):

1. A **stamp-based dedup**. Add `this.stamp = 0` in the constructor. Give every
   item inserted into the grid a mutable `_seen` field (initialised to `-1` at
   insert time in `rebuildSpatialGrid`). To dedup, bump `this.stamp++` at the
   start of a traversal and skip any item whose `item._seen === this.stamp`,
   otherwise set it and process. This replaces `new Set()` entirely.

2. A method `getCell(cx, cy)` that returns `this.cells.get(cx + ',' + cy)` or
   `undefined` — cell-index based, not world-coordinate based, because DDA works
   in cell indices.

> Note: `rebuildSpatialGrid()` already creates one fresh item object per trace
> segment / organelle / vesicle / virus each frame, so adding `_seen: -1` there is
> free. Do not add `_seen` to the raw game objects (`org`, `v`, `vp`) — only to
> the wrapper items the grid stores.

### Step 2 — Rewrite the body of `raycast()` as a DDA walk

Standard Amanatides–Woo traversal over the grid:

```
dirX = cos(angle), dirY = sin(angle)
cx = floor(startX / cellSize),  cy = floor(startY / cellSize)
stepX = dirX > 0 ? 1 : -1       (handle dirX === 0: tMaxX = Infinity, tDeltaX = Infinity)
stepY = dirY > 0 ? 1 : -1       (same for dirY === 0)
tDeltaX = abs(cellSize / dirX)
tDeltaY = abs(cellSize / dirY)
tMaxX = distance along the ray to the first vertical cell boundary
tMaxY = distance along the ray to the first horizontal cell boundary
t = 0                            // distance travelled so far, in world units
```

Loop while `t <= maxDist`:

1. Compute `tExit = min(tMaxX, tMaxY, maxDist)` — the distance at which the ray
   leaves the current cell.
2. **Cheap analytic checks first**, evaluated over the sub-segment
   `[t, tExit]` of the ray. Sample these at a coarse step (16px is fine — they are
   smooth fields, not thin geometry):
   - `isOutsideCell` boundary
   - nucleus core radius
   - mitosis sweep-ring
   If any triggers, return immediately with the distance at which it triggered.
3. **Grid items in this cell.** `getCell(cx, cy)`; for each item not already
   stamped, run the *analytic* segment test against the ray sub-segment:
   - trace → `segSegDistSq(rayAx, rayAy, rayBx, rayBy, item.x1, item.y1, item.x2,
     item.y2) < TRACE_HITBOX²`, where `(rayA, rayB)` is the ray restricted to
     `[t, tExit]`. To get the *distance* of the hit, see Step 3.
   - lysosome / virus / vesicle → `ptSegDistSq(centre, rayA, rayB) < r²`
   - mitochondrion → un-rotate both ray endpoints into organelle-local space, then
     `segSegDistSq` against each of the 5 spine sub-segments (same loop as the
     current code, but with the ray segment instead of a point)
4. Track the **nearest** hit found within this cell (smallest distance), because a
   cell can contain several items. Return it before advancing.
5. Advance: `if (tMaxX < tMaxY) { t = tMaxX; tMaxX += tDeltaX; cx += stepX; }
   else { t = tMaxY; tMaxY += tDeltaY; cy += stepY; }`

Return `{ dist: maxDist, type: 'clear' }` if the loop ends without a hit.

### Step 3 — Getting the hit distance from an analytic test

You need a distance, not just a boolean. Use one shared helper — add it next to
`segSegDistSq`:

```
// Returns the smallest t in [0,1] at which the segment (ax,ay)->(bx,by)
// comes within `r` of the segment (cx,cy)->(dx,dy), or -1 if it never does.
function raySegT(ax, ay, bx, by, cx, cy, dx, dy, r)
```

A binary-search implementation is acceptable and is the recommended one here:
confirm `segSegDistSq(...) < r²` for the full sub-segment first (cheap reject),
then bisect ~8 times on the sub-segment endpoint to find the entry parameter.
8 iterations over a ≤128px cell resolves to ~0.5px, well below the 2.4px hitbox.
Do not over-engineer an exact quadratic solve.

Use the same helper for point targets by passing a degenerate segment
(`cx==dx, cy==dy`).

> `raySegT` is reused by T02 for the ER/Golgi walls. Write it once, generally.

### Step 4 — Hoist the per-item `players.find()`

Inside the trace branch, `players.find(op => op.id === item.playerId)` runs per
item. Since the only reason to call it is the caster's own self-immunity check,
guard it: only look up when `casterId !== null && item.playerId === casterId`,
and hoist the caster object to a local before the loop.

---

## Files touched

`260703_Cellsnake.html` only:

- `class SpatialGrid` — add `stamp`, `getCell()`
- `rebuildSpatialGrid()` — add `_seen: -1` to the four item literals
- new function `raySegT(...)` near `segSegDistSq`
- `function raycast(...)` — body rewritten

Do not touch `checkCollision`, `checkArcCollision`, `updateBotAI`, or
`getRayWeight` in this task.

---

## Verification

1. Console clean on load and through a 60s round.
2. **Behaviour parity.** Before you change anything, add a temporary
   instrumentation block that logs, for a fixed seed of ray inputs, the
   `{dist,type}` results of the old function. Keep the old function under a
   temporary name `raycastOld` while developing, compare the two over one full
   round for the same inputs, and confirm `type` matches and `dist` differs by
   ≤ 12px (the old sampler quantised to 12px; DDA is exact, so DDA's distance
   should be ≤ the old one). Delete `raycastOld` and all instrumentation before
   committing.
3. **Performance.** Wrap the three `raycast` calls in `updateBotAI` with
   `performance.now()`, run 1 player + 3 bots for 60 seconds, log mean µs per
   frame. Record before/after in the commit message. Expect a clear reduction;
   if it is not faster, the DDA is wrong — most likely you are still allocating.
4. **Allocation check.** Chrome DevTools → Performance → record 20s with 3 bots.
   The Memory sawtooth amplitude must be visibly smaller than before. Note it.
5. Bot survives ≥ 30s in a solo-with-bot round without immediately hitting a wall.
6. Regression sweep from `AGENT_CONDUCT.md` §7.6 (you touched a collision-adjacent
   path).

## Definition of done

- [ ] No `new Set()` and no array literal inside any per-step or per-cell loop
- [ ] `raycast` signature and return shape unchanged
- [ ] All hit constants unchanged
- [ ] Parity comparison run and reported
- [ ] Before/after timing in the commit message
- [ ] `raycastOld` and instrumentation removed
- [ ] `docs/TASKS.md`: T01 → `DONE`, T02 → `READY`

## Rollback

Single commit, revertible with `git revert`. If parity cannot be demonstrated,
revert and record why in the task file under `## Blocked`.
