# T63 — Cell B's membrane kept the pre-T62 zoom collapse

**Track:** K · **Depends on:** T62 · **Risk:** low (draw path only) · **Est. diff:** ~45 lines

Owner request, 2026-08-14, from the backlog item T62 section 2 filed against
itself: *"Can we correct for Cell B's membrane during mitosis the zoom problem?"*

---

## Cause

T62 section 2 gave the membrane a low-zoom treatment — `zoomBoost` on every
stroke width, an inward glow, an outward falloff, and (section 6) a breathing
pulse — all inside `drawCalcification()`, which clears and redraws `calcifyLayer`
**every frame** and can therefore read a live `world.scale.x`.

Cell B's wall was not drawn there. It was three `lineStyle`/`drawEllipse` calls
**baked once** into a static `Graphics` (`cellBBg`) at the moment mitosis
triggers, added to `backgroundLayer` and never touched again:

```js
cellBBg.lineStyle(15, 0x1e3799, 0.4);   // flat world-space widths,
cellBBg.lineStyle(8,  0x4a69bd, 0.8);   // baked before the camera
cellBBg.lineStyle(3,  0x82ccdd, 1.0);   // has moved
```

A static `Graphics` cannot respond to zoom, so Cell B kept exactly the behaviour
T62 section 2 existed to remove: at playing zoom (~0.5) its three layers
collapsed into one thin line while the primary cell beside it rendered as a
thick, glowing, breathing wall. Two walls, same event, visibly different — the
worst possible place for the inconsistency, since mitosis is when both are on
screen at once.

## Fix

Extract the membrane treatment into `drawMembraneRings(gfx, cx, cy, a, b,
zoomBoost, glowSteps, breathePx, innerColor, innerAlpha)` and call it **twice**
from `drawCalcification()` — once for `activeCell`, once for `mitosis.cellB`
while `mitosis.state !== 'idle'`. `cellBBg` keeps only its dark interior fill.

One definition of "what a membrane looks like", two callers — so the next change
to the wall cannot apply to one cell and not the other, which is how this
happened.

**Radii:** Cell B uses `activeCell`'s, exactly as the old bake did.
`updateCalcification()` is gated on `mitosis.state === 'idle'`, so the radii
cannot move during the event — the same assumption the bake already relied on,
now made explicit in a comment rather than implied by the baking.

**Deliberately not fixed here:** `mitosis.cellB` still has no `radiusX`/`radiusY`
fields, so `updateVesicles()`'s wall-bounce still reads `NaN` for Cell B (backlog
item, 2026-08-06). Adding those fields would change vesicle *behaviour* around
Cell B, which is a gameplay change and outside a draw-path fix. Left open.

## Verification

- Console clean; no page errors.
- **Cell B and the primary cell screenshotted separately at the same 0.5 zoom**
  (`/tmp/verify/t63-cellB-at-0.5.png`, `t63-primary-at-0.5.png`): the two walls
  are now indistinguishable in treatment — same layered thickness, same inward
  glow, same outward halo. Before, Cell B was a single thin stroke.
- Bridge close-up at 0.5 (`t63-cellB-playingzoom.png`): both walls carry the
  treatment and neck symmetrically into T62 section 3's hourglass.
- `worldChildren` **17 before the event and 17 during** — the bake lost three
  draw calls, gained none; no new display object.
- Quality tiers still respected: `glowSteps` comes from
  `QUALITY_TIERS[quality].membraneGlowSteps`, so `low` drops the glow on **both**
  cells, as it already did on one.
- `node --check` on the extracted script passes.
- No gameplay change: `checkCollision`, `checkArcCollision`, `raycast` and
  `rebuildSpatialGrid` do not appear in the diff, and no hazard constant moved.
  The ring drawn at exactly `(a, b)` is still pinned to the true collision
  boundary and still never takes `breathePx`.

## Definition of done

- [x] One shared `drawMembraneRings()`, called for both cells
- [x] `cellBBg` reduced to its fill
- [x] Cell B matches the primary wall at playing zoom — screenshots
- [x] `worldChildren` unchanged; tiers respected
- [x] No collision or hazard constant touched
- [x] `docs/TASKS.md`: T63 → `DONE`
