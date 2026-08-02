# T12 — Gen 2: membrane calcification

**Track:** C · **Depends on:** T11 · **Risk:** high (touches the arena boundary) · **Est. diff:** ~70 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

From generation 2 onward, shrink the cell membrane frame by frame, closing the
arena over the course of the round.

Roadmap 3.1:

> Frame-by-frame shrinking of the elliptical membrane radii
> (`activeCell.radiusX`/`radiusY`).

---

## Why this is the highest-risk task in Track C

`activeCell.radiusX` and `radiusY` are read by a lot of code that assumes they
are **constant for the round**. Before writing anything, search for every read of
`radiusX` and `radiusY` and list them. At minimum you will find:

- `isOutsideCell()` — the boundary test (correct, will follow the shrink)
- `generateMap()` — background ellipse, membrane rings, protrusion placement,
  cytosol particle placement, organelle spawn bounds. **These are drawn once and
  will not shrink with the value.**
- `updateDriftingOrganelles()` — the wall bounce and the failsafe snap
- `raycast()` and `isInsideNucleus()` — the mitosis sweep-ring positions
- `updateMitosis()` — bridge geometry, `cellB` placement, microtubule extents
- `updateCamera()` — indirectly, via player positions

**The visual membrane is baked into a `Graphics` in `generateMap()`.** If you only
shrink the number, the drawn membrane stays put and players die in open space —
the exact "invisible wall" failure this project has already had twice. Trap §4.4:
physics is authoritative, but here the *visual* must be re-derived every frame to
match.

---

## Design

### 1. State

Add to `activeCell`, initialised in `startRound()`:

```
activeCell.baseRadiusX = 1400;   // the pristine radii for this round
activeCell.baseRadiusY = 1200;
```

Keep `radiusX`/`radiusY` as the **live** values everything else already reads —
that way no other call site changes.

### 2. Shrink rule

In `gameLoop`, gated on `genAtLeast(2)` and only while the cell is not frozen
(reuse the existing `isCellFrozen` flag):

```
const CALCIFY_RATE   = 6;    // px per second of radiusX; radiusY scales proportionally
const CALCIFY_FLOOR  = 0.45; // never shrink below this fraction of base
```

Shrink `radiusX` by `CALCIFY_RATE * deltaSec` and `radiusY` by the same *fraction*
so the ellipse keeps its aspect ratio. Clamp at
`baseRadius * CALCIFY_FLOOR`.

**Do not shrink during a mitosis event.** The bridge and `cellB` geometry are
computed from the radii at event start; shrinking mid-event will detach the bridge
from the cell. Gate on `mitosis.state === 'idle'`.

The floor matters: the nucleus core is lethal out to 130px and organelles are
pushed to a 380px ring, so a membrane below ~600px radius leaves almost no
playable area. `0.45 × 1400 = 630`. Verify that number still leaves a playable
ring after you have watched it.

### 3. Redraw the membrane every frame

The membrane must be re-drawn, not re-created. Add a dedicated `PIXI.Graphics`
for the calcified boundary, created **once** at init (next to the other layer
declarations, added to `backgroundLayer` or its own layer above it), and in
`gameLoop` do `calcifyLayer.clear()` then redraw the three ellipse rings at the
current radii — mirroring the styling already in `generateMap()`.

**Do not** call `generateMap()` per frame, and **do not** create a new `Graphics`
per frame. Both are guaranteed to leak or tank the frame rate.

The baked membrane from `generateMap()` will now be inside the shrinking one.
Options, cheapest first:
- Leave it — it reads as the "old" cell wall the calcification is closing in from.
  Try this first; it may look correct for free.
- If it looks wrong, hide the baked membrane rings when `genAtLeast(2)` and let
  `calcifyLayer` own the boundary entirely.

Pick by looking at it. Record which you chose.

### 4. Push things inward

Anything now outside the shrunken boundary must be handled, not left stranded:

- **Organelles**: `updateDriftingOrganelles()` already calls `isOutsideCell()` and
  snaps them back. Confirm it does so using the *live* radii — read it. It uses
  `nearestCell.radiusX`, so it should follow automatically. Verify.
- **Vesicles**: check whether `updateVesicles()` bounds them. If it does not, they
  will end up outside the wall and be uncollectable. Add a clamp.
- **Players**: a player caught outside the shrinking wall should die to it — that
  is the mechanic. `isOutsideCell()` handles it. **But** the swept collision test
  in `checkCollision` uses the boundary at the *current* frame, so a player
  standing still as the wall passes over them will die correctly. Confirm.
- **Traces** outside the wall: harmless, they just sit there. Leave them.

### 5. Bot awareness

The bot already senses `'boundary'` through `raycast()`'s `isOutsideCell()` call,
so it follows the shrinking wall for free. Verify this rather than assuming —
watch a bot at Gen 2 for 60 seconds and confirm it retreats inward.

---

## Files touched

`260703_Cellsnake.html` only: `activeCell` base radii, `startRound()` reset, new
`calcifyLayer` at init, shrink + redraw block in `gameLoop`, possibly a vesicle
clamp in `updateVesicles()`.

---

## Verification

1. Console clean.
2. **Gen 1 is untouched.** Play a full Gen 1 round. The membrane must not move at
   all. Compare a screenshot at t=0 and t=60s.
3. **Gen 2 shrinks visibly.** `window.setGeneration(2)`, watch 60s. The wall
   closes smoothly with no stepping or flicker.
4. **Visual and lethal boundary agree.** This is the critical test. At Gen 2,
   every 15 seconds, drive a player slowly into the wall from inside. Death must
   occur exactly at the drawn edge — not before, not after. Repeat at four
   compass points (the ellipse is not circular, so test all four).
5. **Floor holds.** Fast-forward to the floor. The membrane must stop and the
   game must remain playable.
6. **Mitosis is unaffected.** Trigger a mitosis event at Gen 2. The bridge must
   attach correctly to both cells, and shrinking must pause for the duration.
7. **Organelles and vesicles stay inside.** Watch for 60s at Gen 2 — nothing may
   be left outside the wall.
8. **Bot retreats.** A bot at Gen 2 must not be crushed against the wall
   passively.
9. **No leak.** With T04's HUD, confirm `worldChildren` is flat over a 5-minute
   Gen 2 round — proving you are redrawing one `Graphics`, not creating many.
10. Regression sweep from `AGENT_CONDUCT.md` §7.6.

## Definition of done

- [ ] Full list of `radiusX`/`radiusY` readers written into this file under `## Call sites`
- [ ] Shrink gated on `genAtLeast(2)`, paused during mitosis and freezes
- [ ] Membrane redrawn each frame into one persistent `Graphics`
- [ ] Visual edge and lethal edge verified identical at four compass points
- [ ] `worldChildren` flat over 5 minutes
- [ ] Gen 1 behaviour bit-identical to before
- [ ] `docs/TASKS.md`: T12 → `DONE`

---

## Call sites

*(Fill in during the task: every place that reads `activeCell.radiusX` or
`radiusY`, and whether it needed a change.)*
