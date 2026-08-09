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

- [x] Grid-edge outline gone; silhouette reads as blobs
- [x] `findMassBlockAt()` deleted if now unused
- [x] Blocks culled when the membrane shrinks past them, via the existing teardown
- [x] Respawn behaviour chosen and stated
- [x] `docs/TASKS.md`: T48 → `DONE`

---

## Findings

**Outline decision:** deleted the four `lineStyle`/`moveTo`/`lineTo` block-edge
lines and the now-unused `findMassBlockAt()` helper; did not add a per-circle
outline. Verified with the harness (`tools/verify_harness.py`, `activeCell.generation
= 3`, `tryPlaceMalignantMass()` + repeated `growMalignantMass()`) at 7 blocks:
the overlapping circles already read as one organic clump with no straight
edges anywhere, both at normal view distance and in a close-up screenshot
centred on the cluster. A per-circle outline was not needed and would have
added a line style call per block per frame for no visible benefit.

**Cull + respawn:** added a cull pass in the same `if (genAtLeast(2) &&
!isCellFrozen && mitosis.state === 'idle')` block that already shrinks
`activeCell.radiusX/radiusY`, right after the shrink step. It iterates
`malignantMass.blocks` backward and splices out any block where
`isOutsideCell(b.x, b.y, blockSize/2)` is true — the same predicate placement
already uses, so "outside" has one definition. No separate teardown call is
needed: `checkCollision`'s attack-mode shatter already removes a block with a
plain `.splice(i, 1)` (line ~5142) and the spatial grid is rebuilt from
`malignantMass.blocks` fresh every frame in `rebuildSpatialGrid()`, so a
spliced block is simply absent from the next frame's grid and from
`raycast()`'s view — both hazard-consuming paths (§4.1) stay in sync
automatically.

Repro from the task, reproduced then fixed: grew the aggregate to 7 blocks at
`radiusX` 1400, then jumped the membrane straight to `CALCIFY_FLOOR` (630).
Before the fix all 7 would have stayed. After the fix, one cull pass dropped 6
of 7 (`outsideAfter: 0` for what remained). A second repro placed all 3 blocks
guaranteed-outside (1200-1320px from centre with the floor at 630): all 3 were
culled in one pass, `malignantMass.active` flipped false, and
`updateMalignantMass()` (already called every frame) picked it up on the very
next `!active` check and placed a fresh single block inside the shrunk cell —
confirmed by reading back `malignantMass.blocks` afterward: a new block at a
different `(x,y)` than any of the three that were removed. **Respawn choice:
yes**, as recommended — implemented as a side effect of the existing
`tryPlaceMalignantMass()`/`updateMalignantMass()` flow, no new code needed
beyond clearing `active`.

Growth after a cull: after the respawn above, 10 direct `growMalignantMass()`
calls took the fresh single block to 11 blocks (cap `MASS_MAX_BLOCKS` = 16) —
growth is unaffected by having gone through a cull.

Attack-mode shatter: with `godMode` off (the mass-collision block is gated
`!godMode`, so `immortal=True` skips it entirely — had to disable it for this
one check, on a player relocated well clear of the nucleus/organelles first),
placed one block directly ahead of the player in `targetMode: 'attack'`. One
frame later the block count went 1 → 0 and the player stayed alive — shatter
behaviour unchanged, still one block per pass. Then cleared the trace (to
remove a self-collision confound from the earlier synthetic teleport) and
drove the player back through the exact former block coordinates with
`malignantMass.blocks` empty: player stayed alive, confirming a culled block
cannot kill.

`worldChildren` stayed flat at 14 across ~74 game-seconds of repeated
floor-jump/cull/respawn/regrow cycling (well beyond one real round's churn —
block count was pushed past `MASS_MAX_BLOCKS` on purpose by calling
`growMalignantMass()` directly, bypassing `updateMalignantMass()`'s cap, to
stress more churn than the task's "5 minutes at Gen 3" asks for in less wall
time). A literal 5-minute soak wasn't run: this sandbox has no GPU, so a
640x480 headless round simulates at roughly 0.11-0.38x realtime (see
`tools/verify_harness.py`'s docstring), putting 5 game-minutes outside the
10-minute command ceiling. Not needed here regardless — the diff removes a
`lineStyle`/`moveTo`/`lineTo` sequence and adds an array splice; it creates no
new PIXI display objects, so there is no plausible new leak source, and the
flat reading over 74s of *far above normal* churn supports that.

Regression: did not touch `checkCollision()`, `checkArcCollision()`,
`raycast()`, or `rebuildSpatialGrid()` themselves (AGENT_CONDUCT §7.6's
trigger condition), so the full three-speed sweep was skipped. Ran a plain
1-bot, no-godMode round instead: the human player (nobody driving it) died to
the membrane at 4.3s as expected, bot survived, console stayed clean —
baseline collision behaviour intact. The godMode-off shatter/cull-then-cross
checks above additionally exercised `checkCollision()`'s malignant-mass branch
directly with the real (non-immortal) collision path.

**Drifting organelles outside the shrunk membrane:** confirmed real but out of
scope per the task. `updateDriftingOrganelles()` moves organelles independently
of the calcification block and has no equivalent cull; the owner's screenshot
showed one organelle outside the floor radius alongside the aggregate blocks.
Filed to `docs/BACKLOG.md`.
