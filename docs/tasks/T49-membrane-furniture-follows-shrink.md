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

- [ ] Protrusions ride the shrinking wall, with the radii-unchanged early-out
- [ ] `cellBg` follows too; still one persistent `Graphics`
- [ ] Cytosol blobs contained
- [ ] Gen 1 unchanged
- [ ] `docs/TASKS.md`: T49 → `DONE`

---

## Findings

*(Counts before/after, the per-frame cost, and how cytosol containment was done.)*
