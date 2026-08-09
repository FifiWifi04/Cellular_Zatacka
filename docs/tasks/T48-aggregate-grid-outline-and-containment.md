# T48 — The aggregate is drawn in a rectangular frame, and it survives outside the membrane

**Track:** J · **Depends on:** T39 · **Risk:** low-medium · **Est. diff:** ~35 lines

Owner report, 2026-08-09, with a screenshot of a Gen 3 round: *"ideally we would
remove the rectangular framing of aggregates and they grow outside of shrinking
membrane."* Both are visible in one frame — amber blobs sitting inside a hard
tan rectangle, in a region the membrane has already retreated from.

---

## Problem 1 — the outline is the grid, not the silhouette

T39 replaced the square blocks with irregular blobs, but kept an outline pass
that still traces **the square cell edges**:

```js
massLayer.lineStyle(3, 0x4a3a18, 1.0);
if (!findMassBlockAt(b.cx, b.cy - 1)) { massLayer.moveTo(b.x - half, b.y - half); massLayer.lineTo(b.x + half, b.y - half); }
// ...three more, one per unoccupied 4-neighbour
```

Skipping shared edges makes it one connected boundary — which is why it reads as
a *frame* rather than as separate boxes — but it is still an axis-aligned
rectilinear polygon around a set of grid cells, with the soft blobs floating
loose inside it. The blobs never touch it, so it does not even read as their
outline.

**Fix:** delete the four `lineStyle`/`moveTo`/`lineTo` block-edge lines. The
blobs already merge into one clump because neighbouring blocks' circles overlap;
that overlap is the silhouette. If a defining edge is still wanted after seeing
it bare, outline each **circle** instead (`lineStyle` before the `drawCircle`
calls, same dark ochre) so the line follows the shape the player actually sees.
Screenshot both and pick — put the screenshots in `## Findings`.

`findMassBlockAt()` exists only for this outline. If nothing else calls it after
the change, delete it too rather than leaving a dead helper.

## Problem 2 — blocks stay put while the membrane retreats past them

`tryPlaceMalignantMass()` and `growMalignantMass()` both check
`isOutsideCell(x, y, half)` **at placement time**. From Gen 2 the membrane
shrinks continuously toward `baseRadiusX * CALCIFY_FLOOR`, and nothing ever
re-checks blocks that are already placed.

Measured: with the aggregate grown to 4 blocks at `radiusX` 1324, jumping the
membrane to its floor (630) leaves **4 of 4 blocks outside it** — plus one
organelle. The aggregate is then unreachable dead geometry drawn over the dead
zone outside the cell, exactly as in the screenshot.

**Fix:** each time the membrane shrinks, drop blocks that are now outside it.
Do this in the calcification block that already changes the radii, not in the
draw path (§4.4a), and reuse `isOutsideCell(b.x, b.y, half)` so there is one
definition of "outside". Removal must go through whatever teardown the shatter
path uses so the spatial-grid entry does not go stale mid-frame (§4.1) — check
how the T14 attack-mode shatter removes a block and match it.

Two follow-on decisions to make and state:

- **If every block is culled**, does the aggregate respawn? Recommended yes —
  clear `malignantMass.active` so `updateMalignantMass()` re-places it inside
  the smaller cell. Gen 3+ without its hazard is a soft round.
- **Organelles** are drifting entities and one was also outside at the floor.
  That is a different subsystem (`updateDriftingOrganelles`) — **out of scope
  here**; note it in `## Findings` and file it if it is real.

## Verification

1. Console clean.
2. Screenshot of a Gen 3 aggregate at 4+ blocks: **no straight lines anywhere**
   in the clump. Compare against the owner's screenshot.
3. Force the membrane to `CALCIFY_FLOOR` with the aggregate grown; **0 blocks
   outside**, and the culled ones are visually gone, not just untested.
4. Growth still works after a cull — the aggregate regrows inside the smaller
   cell up to `MASS_MAX_BLOCKS`.
5. Attack-mode shatter still removes exactly one block per `MASS_HIT_COOLDOWN`,
   and a culled block cannot kill (drive through where one used to be).
6. `worldChildren` flat over 5 minutes at Gen 3.
7. Regression sweep §7.6.

## Definition of done

- [ ] Grid-edge outline gone; silhouette reads as blobs
- [ ] `findMassBlockAt()` deleted if now unused
- [ ] Blocks culled when the membrane shrinks past them, via the existing teardown
- [ ] Respawn behaviour chosen and stated
- [ ] `docs/TASKS.md`: T48 → `DONE`

---

## Findings

*(Before/after screenshots, outline decision, cull + respawn behaviour, and
whether drifting organelles outside the shrunk membrane is a real second bug.)*
