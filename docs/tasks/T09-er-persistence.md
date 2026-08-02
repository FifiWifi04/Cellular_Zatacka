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

- [ ] `window.erData` caches the ER layout for the round
- [ ] Reset alongside `window.golgiData` in `generateMap()`
- [ ] Shattered layers still disappear and stop being lethal
- [ ] No `Math.random()` remains in the ER draw path on redraws
- [ ] Screenshot comparison before/after a shatter attached to the commit message
- [ ] `docs/TASKS.md`: T09 → `DONE`
