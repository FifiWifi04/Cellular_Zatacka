# T02 — Wall sensing: microtubules + ER/Golgi

**Track:** A (Phase 1 gate) · **Depends on:** T01 · **Risk:** medium · **Est. diff:** ~90 lines

Read `docs/AGENT_CONDUCT.md` before starting. This task is the canonical example
of trap §4.1 — a hazard that exists in the physics path but not the sensor path.

---

## Goal

Make the bot's ray sensor detect the two lethal structures it is currently blind
to, and fix the point-in-time microtubule collision test in `gameLoop` so it is
swept like every other hazard.

## Why

Roadmap 1.1 requires the sensor to detect **microtubules** as a lethal boundary.
Today `raycast()` sees membrane, nucleus, sweep-ring, traces, organelles, viruses
and vesicles — but not:

1. `mitosis.microtubules` — axis-aligned rectangles in the bridge, lethal while
   `mitosis.state !== 'idle' && mitosis.currentWidth > 350`, killed in `gameLoop`
   under the comment `// 1.5 Microtubule Scaffolding Collision`.
2. `centralHitboxes` — the ER and Golgi walls, lethal via `checkArcCollision()`.

The bot therefore steers confidently into structures it cannot see. Until this
lands, Phase 1.1 is not spec-complete.

While here, the microtubule physics test is a **point-in-time AABB check** on
`(nextX, nextY)` only. At Very Fast speed the head moves ~3.5px/frame against a
20px-thick tube, so it mostly works — but it is the one remaining unswept test in
the codebase and it will tunnel once anything makes the step longer (the fuzzer's
4× time dilation already does exactly that). Fix it here.

---

## Prerequisites

Read in full:

- `updateMitosis()` — the `// GENERATE MICROTUBULES` block. Tubes are
  `{x, y, w, h}` **world-space AABBs**, 2 of them, 20px thick.
- `gameLoop()` — the `// 1.5 Microtubule Scaffolding Collision` block, including
  its exact activation condition.
- `checkArcCollision()` — note the `-globalRotation` un-rotation and that
  `centralHitboxes` entries are **cell-local, un-rotated** (trap §4.3).
- `drawArcs()` — note that only `{type:'path', points, thick}` entries are ever
  pushed into `centralHitboxes`. The `type === 'poly'` branch in
  `checkArcCollision` is dead code. **Leave it alone** (log it in
  `docs/BACKLOG.md`); do not delete it in this task.
- `raySegT(...)` from T01 — you will reuse it.

---

## Part 1 — Microtubule sensing in `raycast()`

Microtubules are world-space AABBs, so no frame conversion is needed.

1. Add a guard identical to the physics one, evaluated **once at the top of
   `raycast`**, not per step:

   ```
   const tubesLive = (mitosis.state !== 'idle' && mitosis.currentWidth > 350);
   ```

2. If `tubesLive`, test the **whole ray segment** — from `(startX, startY)` to
   `(startX + cos*maxDist, startY + sin*maxDist)` — against each tube's AABB
   expanded by `TRACE_HITBOX`, using a slab test that returns the entry distance
   `tEnter` in world units. Two tubes, so this is O(2) per ray — do **not** put
   this inside the DDA cell loop.

3. Keep the resulting `{dist: tEnter, type: 'microtubule'}` as a **candidate**
   and, at the end, return whichever of (DDA hit, microtubule hit, wall hit from
   Part 2) has the smallest `dist`.

   > Structure the function so the analytic tests run first, produce a
   > `maxDist` clamp, and the DDA then only needs to march up to that clamp. That
   > is both correct and faster.

## Part 2 — ER/Golgi wall sensing in `raycast()`

`centralHitboxes` lives in the cell-local un-rotated frame. Un-rotate the **ray**,
not the walls — the walls are many points, the ray is two.

1. Compute once per `raycast` call:

   ```
   cosG = cos(-globalRotation), sinG = sin(-globalRotation)
   // ray start, un-rotated into cell-local space
   dxA = startX - activeCell.x,  dyA = startY - activeCell.y
   uAx = dxA*cosG - dyA*sinG,    uAy = dxA*sinG + dyA*cosG
   // ray end, same transform
   ```

   Because rotation is rigid, distances are preserved: a `t` found in the
   un-rotated frame is the same world distance. No rescaling needed.

2. For each `hb` in `centralHitboxes` with `hb.type === 'path'`, for each
   consecutive point pair, call
   `raySegT(uAx, uAy, uBx, uBy, p1.x, p1.y, p2.x, p2.y, hb.thick/2 + TRACE_HITBOX)`
   and keep the smallest non-negative `t`. Multiply by `maxDist` to get world
   distance.

3. Emit type `'wall'` for these hits.

4. **Skip the whole block when the ER/Golgi have been destroyed.** After the
   mitosis laser crosses the nucleus centre, `nucleusLayer.visible` and
   `golgiERContainer.visible` are set to `false` — but `centralHitboxes` is *not*
   cleared, and `checkArcCollision` keeps killing players against invisible walls.

   **This is a real bug and it is in scope for this task.** In
   `drawMitosisVisuals()`, at the same place that sets those two `.visible = false`
   and spawns the 15-vesicle burst, also do `centralHitboxes = [];`. Then both the
   physics and the sensor agree with what the player can see. Verify explicitly
   (see Verification 4).

   > Guard it the same way the burst is guarded (`if (nucleusLayer.visible)`) so it
   > runs exactly once, and make sure the `else` branch that restores
   > `.visible = true` does not need to restore hitboxes — confirm by reading it.
   > If the `else` branch can re-run after destruction, restoring visibility
   > without hitboxes would desync the other way; if so, set a one-way
   > `mitosis.nucleusDestroyed = true` flag and gate both branches on it.

## Part 3 — Sweep the microtubule physics test

In `gameLoop`, replace the AABB point test on `(nextX, nextY)` with a swept test
of the segment `(p.x, p.y) → (nextX, nextY)` against the tube AABB expanded by
`TRACE_HITBOX`. Reuse the same slab helper you wrote for Part 1 — write it once
as a module-level function, e.g.:

```
// smallest t in [0,1] where segment A->B enters the AABB expanded by pad,
// or -1 if it never does
function segAabbT(ax, ay, bx, by, rx, ry, rw, rh, pad)
```

Keep every surrounding condition identical (`mitosis.state !== 'idle'`,
`!p.isGap`, `!isGhost`, `!devMode`, `mitosis.currentWidth > 350`). Do not change
the `!devMode` guard — T04 owns that.

## Part 4 — Weights for the new hit types

In `getRayWeight()`, add `'microtubule'` and `'wall'` to the same hazard branch as
`'boundary'`/`'nucleus'`/`'trace'`/`'organelle'`/`'virus'`. Use the identical
formula — **do not** invent new tuning here. T03 rewrites this function entirely;
T02 just must not leave the new types falling through to the default `1000`
("clear"), which would make the bot treat walls as safe.

---

## Files touched

`260703_Cellsnake.html` only:

- new `segAabbT(...)` helper near `segSegDistSq`
- `raycast()` — analytic microtubule + wall pre-pass, `maxDist` clamp
- `getRayWeight()` — two new type strings in the hazard branch
- `gameLoop()` — microtubule check swept
- `drawMitosisVisuals()` — clear `centralHitboxes` on nuclear destruction

---

## Verification

1. Console clean.
2. **Bot sees microtubules.** Enable dev mode, fast-forward to mitosis
   (`Tab` repeatedly, or `F`), run 1 player + 1 bot, and watch the bot cross the
   bridge. It must steer into the open central lane between the two tubes rather
   than driving into a tube. Compare against a pre-change run — the difference
   should be obvious.
3. **Bot sees ER/Golgi.** Start a normal round with 1 bot. The bot must stop
   colliding with the ER/Golgi ring around the nucleus. Watch for 60s.
4. **Invisible-wall fix.** Fast-forward through a full mitosis until the nucleus
   and ER/Golgi visually disappear. Then drive a human player straight through
   the empty space where the ER used to be. You must **not** die. Before this
   task, you would.
5. **Swept tubes.** With dev mode + `F` (4× dilation) active and god mode
   temporarily disabled, drive at a tube head-on at Very Fast speed. Death must
   trigger; the head must not appear on the far side.
6. Regression sweep from `AGENT_CONDUCT.md` §7.6.
7. Confirm you changed **both** the sensor and the physics path, and say so in the
   commit message.

## Definition of done

- [ ] `raycast` returns `'microtubule'` and `'wall'` hit types
- [ ] Analytic tests run once per ray, not per DDA step
- [ ] Microtubule physics test is swept
- [ ] `centralHitboxes` cleared when the nucleus is destroyed
- [ ] Dead `'poly'` branch left untouched and logged in `docs/BACKLOG.md`
- [ ] `docs/TASKS.md`: T02 → `DONE`, T03 → `READY`
