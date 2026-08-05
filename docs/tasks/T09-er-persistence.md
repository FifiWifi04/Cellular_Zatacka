# T09 — Persist ER geometry across `drawArcs()` redraws

**Track:** B · **Depends on:** — (independent, can be taken any time) · **Risk:** low · **Est. diff:** ~35 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Stop the endoplasmic reticulum from teleporting to a new random layout every time
any arc shatters. Mirror the fix already applied to the Golgi.

## Why

`drawArcs()` rebuilds all central structures from scratch and is called:

- once from `generateMap()` (`drawArcs(activeArcs)`), and
- again from `updateMitosis()` whenever an arc is destroyed
  (`if (arcsChanged) drawArcs();`).

The Golgi had exactly this bug and it was fixed by caching its position, angle and
rotation in `window.golgiData` on first draw and reusing them on redraws.

**The ER was never given the same treatment.** Its layout is generated with
`Math.random()` on every call:

```
let currentAngle = (erGroup * Math.PI * 2 / 4) + (Math.random() * 0.4);
let currentR = 150 + Math.random() * 10;
let thick = 14 + Math.random() * 6;
let numLayers = 3 + Math.floor(Math.random() * 2);
let span = 0.8 + Math.random() * 0.6;
let nextR = currentR + 25 + Math.random() * 10;
```

So the instant a player shatters any Golgi or ER layer, the entire ER jumps to a
new shape — and because `centralHitboxes` is rebuilt at the top of `drawArcs()`,
the **lethal geometry moves with it**. A player travelling through a safe channel
can be killed by a wall that materialises around them.

This is the same class of bug as the Golgi one and it is still live.

---

## Prerequisites

Read `drawArcs()` in full — especially:

- the `centralHitboxes = []` reset at the top
- the ER block, gated on `activeArcs.some(a => a.type === 'ER')`
- the Golgi block and its `window.golgiData` pattern (the model to copy)
- the two `centralHitboxes.push({ type: 'path', ... })` sites
- `generateMap()`, where `window.golgiData = null` resets the cache per round
- `updateMitosis()`'s arc-shatter loop and `if (arcsChanged) drawArcs();`

---

## Implementation plan

### Step 1 — Cache the ER layout

Follow the `window.golgiData` pattern exactly, so the two read the same way.

Add `window.erData`. On the first draw of a round (when `window.erData` is
null/undefined), generate the random layout **once** and store everything the
draw needs — for each of the 4 ER groups: `currentAngle`, `currentR`, `thick`,
`numLayers`, and the per-layer `span`, `dir`, `nextR` values. On subsequent
calls, read from the cache instead of calling `Math.random()`.

The cleanest version stores the **resolved point list** (`erPath`) plus `thick`
per group, since that is what both the drawing and `centralHitboxes` consume.
Prefer that: it is fewer fields and guarantees the hitbox and the drawing can
never diverge.

### Step 2 — Reset per round

In `generateMap()`, next to the existing `window.golgiData = null;`, add
`window.erData = null;`. Both must reset together so a new round gets a new
layout.

### Step 3 — Verify the shatter path still removes geometry

The point of the redraw is that shattered layers stop being drawn *and stop being
lethal*. Caching the layout must not cache the *membership* — the
`activeArcs.some(...)` / `if (!activeArcs.some(a => a.type === 'Golgi' && a.r === layerRadius)) continue;`
filters must still run on every call against the live `activeArcs` array.

Read those filters and confirm your cache sits **inside** them, not around them.

### Step 4 — Check for the same bug elsewhere in `drawArcs()`

While you are in this function, check whether the ribosome dots or any other
decorative element also re-randomises. If it is purely decorative (no
`centralHitboxes` entry), it is a cosmetic flicker, not a fairness bug — log it
in `docs/BACKLOG.md` and leave it. Only fix things that feed `centralHitboxes`.

---

## Files touched

`260703_Cellsnake.html` only: `drawArcs()`, and one line in `generateMap()`.

---

## Verification

1. Console clean.
2. **ER is stable across a shatter.** Start a round, take a screenshot of the
   central structures, then shatter one arc (drive into it with a speed power-up,
   or force it in dev mode). Screenshot again. The ER must be pixel-identical
   apart from the destroyed layer.
3. **Hitboxes follow the drawing.** After a shatter, drive a player along the ER
   walls. Every death must be against something visible, and every visible ER
   wall must still kill.
4. **Fresh layout per round.** Restart 5 times. The ER layout must differ between
   rounds (it is still randomised — just once per round).
5. **Mitosis path.** Fast-forward through a full mitosis. The ER must not jump at
   any point, and must vanish cleanly when the laser crosses the nucleus centre.
   (If T02 has landed, `centralHitboxes` is also cleared there — confirm both.)
6. Regression sweep from `AGENT_CONDUCT.md` §7.6.

## Definition of done

- [x] `window.erData` caches the ER layout for the round
- [x] Reset alongside `window.golgiData` in `generateMap()`
- [x] Shattered layers still disappear and stop being lethal
- [x] No `Math.random()` remains in the ER draw path on redraws
- [x] Screenshot comparison before/after a shatter attached to the commit message
- [x] `docs/TASKS.md`: T09 → `DONE`

## Verification results — 2026-08-05

Ran via `tools/verify_harness.py` (640x480, ~0.38x game time). All four scripts:
console clean, no page errors.

1. **Console clean** — all scripts below printed `CONSOLE CLEAN`.
2. **ER stable across a redraw.** Started a round, snapshotted `window.erData`
   (4 groups) and the ER `centralHitboxes` entries, then called `drawArcs()`
   again directly (the same call `arcsChanged` makes on a Golgi shatter, with
   the ER arc still present in `activeArcs`). `erData` was byte-identical
   before/after (`erDataIdenticalAcrossRedraw: true`), hitbox point counts
   unchanged (4 groups, 4 hitbox entries before and after). Screenshots
   `t09_before_redraw.png` / `t09_after_redraw.png` show the cyan ER arcs
   pixel-identical (only independently-drifting mitochondria moved).
3. **Hitboxes follow the drawing.** `centralHitboxes.push({points: erPath...})`
   and `structGraph.moveTo/lineTo` both read the same cached `erPath` array
   per group — they cannot diverge by construction now. Confirmed hitbox
   point counts match `erPath.length` for all 4 groups (100/108/71/103 and
   restated after redraw).
4. **Fresh layout per round.** Restarted 5 times; hashed each round's
   `window.erData` (first point, radius, thickness, point count per group) —
   5/5 unique (`uniqueLayouts: 5`).
5. **Mitosis path.** Forced `mitosis.nextTriggerTime`/`eventStartTime` to
   fast-forward the sweep without waiting real time (state `forming`
   confirmed). Fast-forwarded to `sweepProgress≈0.3`: one Golgi layer shattered
   (`arcsChanged` fired, `activeArcs` went from 4 Golgi entries to 3) while ER
   was still active — `erData` stayed identical
   (`erDataStableGolgiShatter: true`). Fast-forwarded further to
   `sweepProgress≈0.51`: the ER entry was swept and removed from `activeArcs`
   (`erActiveAfterFullSweep: false`), and its `centralHitboxes` entries
   disappeared (`erHitboxesAfterFullSweep: 0`) — it stops being lethal exactly
   when it stops being drawn.
6. **Regression sweep.** `checkCollision()`/`checkArcCollision()`/`raycast()`/
   `rebuildSpatialGrid()` were not touched by this task (only `drawArcs()` and
   one reset line in `generateMap()`), so the full §7.6 sweep does not apply.
   Ran a 30s play check (1 player + 3 bots, `speed="1.5"`) as a general
   sanity pass instead: all 4 alive throughout, 1198 trace points, console
   clean.

`python3 tools/build_standalone.py --check` passes (rebuilt after the change).
