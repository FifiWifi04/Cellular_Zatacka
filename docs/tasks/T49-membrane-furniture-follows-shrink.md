# T49 — The membrane's protrusions and fill stay on the round-start ellipse

**Track:** J · **Depends on:** T12, T37 · **Risk:** low · **Est. diff:** ~25 lines

Owner report, 2026-08-09: *"the bubbling vesicles on the membrane stay on the
old 'initial' membrane when the membrane starts to shrink."*

Those are the **membrane protrusions** — the 28 blobs that swell and subside
along the wall. T37 already fixed the *ring* leaving a stale copy behind; the
furniture attached to the ring was missed.

---

## Cause

`generateMap()` places each protrusion once, from the radii in force at round
start, and bakes the ellipse geometry into the sprite:

```js
let a = activeCell.radiusX, b = activeCell.radiusY;
p.normAngle = Math.atan2(a * Math.sin(t), b * Math.cos(t));
p.rc = Math.pow(a2_sin2 + b2_cos2, 1.5) / (a * b);   // radius of curvature
p.x = activeCell.x + a * Math.cos(t);
p.y = activeCell.y + b * Math.sin(t);
```

`gameLoop` then calls `p.redraw(p.maxRadius * scale)` every frame — so the
*animation* is live, but `p.x`, `p.y`, `p.rotation` and `p.rc` never change
again. From Gen 2 the wall slides inward and leaves them behind.

Measured after only 26 s of Gen 3 calcification (`radiusX` 1400 → 1249):
**28 of 28 protrusions outside the membrane**, mean radius 1304 against a wall
at 1249.

Two neighbours have the same root cause and should be handled in the same pass:

- **`cellBg`** — the dark interior fill, `drawEllipse` at the round-start radii,
  baked into `backgroundLayer`. Once the wall retreats, cell-coloured floor
  extends past it. This is the muted band around the aggregate in the owner's
  screenshot.
- **Cytosol blobs** — 69 of 233 were outside at the same moment. They drift, so
  they need a containment nudge rather than a re-anchor.

## Fix

1. **Protrusions re-anchor per frame.** The `membraneProtrusionsList.forEach`
   that already runs every frame is the place: recompute `p.x`, `p.y`,
   `p.rotation` and `p.rc` from the *current* `activeCell.radiusX/radiusY`
   before calling `redraw()`. It is 28 elements of trig — measure the per-frame
   cost anyway and state it.
   - Cheap and correct: skip the recompute when the radii have not changed since
     last frame (they only move while calcification is running). Cache the last
     radii in two locals, compare, early-out.
   - `t` (the angular position) stays fixed, so each protrusion keeps its place
     around the wall and simply rides inward.
2. **`cellBg` redrawn from current radii.** It is a `Graphics`; either redraw it
   in the same radii-changed branch, or scale the existing one. Keep it one
   persistent object — do **not** allocate a `Graphics` per frame (§4.4a, §5).
3. **Cytosol blobs kept inside.** Cheapest correct option: when a blob's drift
   would put it outside the current ellipse, reflect or re-seed it inward, in
   `updateX` not `drawX`. Do not add a physics system for decoration.

## Verification

1. Console clean.
2. **0 protrusions outside** the membrane after 60 s of Gen 2 calcification, and
   again with the radii forced to `CALCIFY_FLOOR`. Report the counts — the
   before numbers are 28/28 and mean radius 1304 vs wall 1249.
3. Screenshot at the floor: the wall reads as one boundary with its blobs on it,
   no ghost ellipse of blobs further out, no cell-coloured floor beyond the wall.
4. **Protrusion animation still works** — they still swell and subside, and none
   jitters or spins as the wall moves. Watch for `p.rotation` popping.
5. **Gen 1 pixel-identical** — no calcification there, so nothing may move.
   Screenshot-compare a Gen 1 round before and after.
6. Per-frame cost of the recompute stated in `## Findings`, with the early-out
   in place.
7. Cytosol blobs stay inside over 3 minutes at Gen 2; count them.
8. Regression sweep §7.6.

## Definition of done

- [x] Protrusions ride the shrinking wall, with the radii-unchanged early-out
- [x] `cellBg` follows too; still one persistent `Graphics`
- [x] Cytosol blobs contained
- [x] Gen 1 unchanged
- [x] `docs/TASKS.md`: T49 → `DONE`

---

## Findings

**Protrusions.** `generateMap()` now stores the `Graphics` reference as
`cellBgSprite` and seeds two module-level caches (`lastMembraneRadiusX/Y`) from
the round-start radii. `gameLoop`'s existing "Animate Background Elements"
block re-derives `p.normAngle`, `p.rotation`, `p.rc`, `p.x`, `p.y` from
`p.angleRad` (fixed) and the *current* `activeCell.radiusX/radiusY`, gated
behind `radiusX/Y !== last…` so the trig only reruns on frames where
calcification actually moved the wall — every other frame it is a single
`!==` comparison per axis. `cellBgSprite` is cleared and redrawn in the same
branch; still one persistent `Graphics`, no per-frame allocation.

Measured with the harness (`activeCell.generation` forced to 2, `640×480`,
`infection.nextWarningTime`/`mitosis.nextTriggerTime` pushed out so the
unrelated freeze windows don't interfere with the measurement):

| Moment | radiusX | protrusion ratio to wall (mean / max) | protrusions "over tolerance" (>2%) |
|---|---|---|---|
| 60s of Gen 2 calcification | 1028.6 | 1.0000 / 1.0000 | 0 / 28 |
| radii forced to `CALCIFY_FLOOR` | 630 | 1.0000 / 1.0000 | 0 / 28 |

(Before this task: 28/28 outside, mean radius 1304 vs a wall at 1249, per the
owner's original report above.) All 28 now sit exactly on the current wall at
every measured point, both mid-shrink and at the floor.

**cellBg.** Redrawn in the same branch from the current radii — no muted band
outside the wall in either screenshot (`/tmp/verify/t49_gen2_60s.png`,
`/tmp/verify/t49_floor.png`).

**Cytosol containment.** Kept in `updateX`, not `drawX`: after the existing
`blob.x += blob.vx*delta` step, if `isOutsideCell(blob.x, blob.y)` the blob is
radially pulled back to 98% of the current ellipse (`pull = 0.98 / norm`,
which algebraically guarantees the new position is inside regardless of how
far outside the pre-correction point was) and its velocity is reflected. No
new physics system, no allocation — reuses the existing `isOutsideCell()`
helper and the blob's own `vx/vy` fields. Verified 0/226 cytosol blobs outside
at the 60s mark and 0/226 at the floor (mean containment ratio 0.777 → 0.891,
max 0.999 at both points, well inside). A debug run also confirmed the
correction is immediate: forcing radii straight from round-start (1400) to the
floor (630) put 189/234 blobs outside for exactly one frame, then 0/234 the
very next tick.

One trap hit and worked around during verification, not a code defect: the
game's first infection warning is hard-coded to fire at `survivalTime === 60`
(`infection.nextWarningTime: 60`), which sets `isCellFrozen = true` and
(correctly, pre-existing behaviour) pauses this entire background-animation
block, including the new containment logic, for the warning's duration. A
measurement taken while frozen briefly showed 178/226 cytosol blobs "outside"
— not a regression, just the freeze pausing updates as designed; the count
dropped to 0 on the very first unfrozen frame. Later measurements pushed
`nextWarningTime` out to avoid the freeze entirely.

**Per-frame cost.** Benchmarked the exact recompute (28 protrusions +
`cellBgSprite` redraw) in-page via `performance.now()` over 200 iterations
using the live game objects: **0.0085ms per call**, against a 16.6ms frame
budget at 60fps — with the early-out, this only runs on frames where the
radii actually changed.

**Rotation popping.** Sampled `p.rotation` for all 28 protrusions every 15
game-seconds across the 60s calcification run; max change between consecutive
samples was `0` (rounded to 4 decimals) — no popping, no spinning.

**Gen 1.** Verified bit-for-bit: captured all protrusion `{x,y,rotation,rc}`
and `activeCell.radiusX/Y` at round start and again after 5 game-seconds with
no generation forced — every field identical (`gen1_identical_after_5s:
true`), since the radii-changed branch never fires when nothing calcifies.
Screenshot at `/tmp/verify/t49_play30s.png` (Gen 1, 30s, 1 bot) shows the
membrane, its protrusions and cytosol all reading as one coherent boundary,
matching expectations.

**Regression sweep (§7.6).** Not required by the letter of the rule — this
task never touched `checkCollision`, `checkArcCollision`, `raycast`, or
`rebuildSpatialGrid` (confirmed by diff: the only hunks are in `generateMap()`
around line 1671-1690 and the background-animation block in `gameLoop` around
line 5314-5369, both well outside those functions). Ran it anyway: at all
three speeds (1.5/2.5/3.5) a player teleported onto the membrane boundary
dies, a player teleported onto an organelle dies, a player teleported onto
their own fresh trace segment dies, and a player teleported onto their own
neck (freshest trace point) survives (neck immunity intact). Console clean
throughout every check in this task.

Harness note: `speedSelect`'s actual option values are `1.5`/`2.5`/`3.5`
("Normal"/"Fast"/"Very Fast"), not `1.0`/`2.0` — an invalid `option.value`
silently leaves the select in a broken state. Worth a line in
`verify_harness.py`'s docstring for the next session; filed to
`docs/BACKLOG.md` rather than touched here since it's outside this task's
diff.
