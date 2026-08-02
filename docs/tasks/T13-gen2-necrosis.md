# T13 — Gen 2: organelle necrosis (lethal static walls)

**Track:** C · **Depends on:** T11 · **Risk:** medium · **Est. diff:** ~80 lines

Read `docs/AGENT_CONDUCT.md` before starting. Pay particular attention to §4.1
(two consumers) and §4.4 (physics is authoritative).

---

## Goal

From generation 2, randomly freeze drifting organelles: they stop moving, turn
stone-grey, and become permanent static walls.

Roadmap 3.1:

> Randomly freeze drifting organelles, turning them stone-gray and switching
> their collision profile to lethal, static walls.

---

## Why this needs care

The roadmap phrase "switching their collision profile" is the trap. Organelles
are **already lethal** — `checkCollision()` kills on contact with any organelle.
So "becoming lethal" is not the change; **becoming static and permanent** is.

The prior conversation flagged this explicitly: a changed collision profile must
flow through the **same swept grid tests you already have**, not a separate path.
Do not add a parallel collision system for necrotic organelles. They stay in
`organelles[]`, stay in `rebuildSpatialGrid()`, and stay in `checkCollision()` and
`raycast()`. Only their *motion* and *appearance* change.

If you find yourself writing a new `checkNecroticCollision()`, stop — the design
is wrong.

---

## Prerequisites

Read: the organelle object literal in `generateMap()`, `createOrganelleGraphics()`,
`updateDriftingOrganelles()`, `rebuildSpatialGrid()`'s organelle insert, the
organelle branches of `checkCollision()` and `raycast()`, and the arc-shatter path
in `updateMitosis()` that destroys an organelle sprite (the correct
destroy pattern).

---

## Design

### 1. State

Add one field to the organelle object: `o.necrotic = false`. Set at creation in
`generateMap()`.

### 2. Freezing

In `gameLoop` (not in `updateDriftingOrganelles` — keep that function about
motion), gated on `genAtLeast(2)`:

```
const NECROSIS_INTERVAL = 12;   // seconds between freeze events
const NECROSIS_MAX_FRAC = 0.5;  // never freeze more than this fraction
```

Every `NECROSIS_INTERVAL` seconds of un-frozen game time, pick one random
**non-necrotic** organelle and set `necrotic = true`, provided the necrotic count
stays under `NECROSIS_MAX_FRAC × organelles.length`.

The cap is not optional. With 25 organelles and no cap, a long round ends with 25
immovable walls in a shrinking arena (T12) and becomes unplayable.

**Do not freeze an organelle that is currently overlapping a player**, or you kill
someone with no warning. Check distance to every alive player's head before
committing the freeze — skip and retry next interval if any player is within, say,
`o.radius + 120`.

### 3. Motion

In `updateDriftingOrganelles()`, at the top of the per-organelle loop:

```
if (o.necrotic) { /* keep sprite synced, skip all physics */ continue; }
```

Be careful with `continue` and the **inner pair-collision loop** (`for j = i+1`).
A necrotic organelle must still push *drifting* ones away, or they will overlap
and look broken. Two options:

- **Preferred:** keep the pair loop running for necrotic `o`, but make the
  resolution one-sided — the drifting organelle takes the whole displacement, the
  necrotic one does not move. Read the existing symmetric resolution and make the
  necrotic side a no-op.
- Simpler but worse: skip the pair loop entirely and accept overlaps.

Take the preferred option and verify visually.

Also zero `o.vx`, `o.vy`, and `o.rotSpeed` at the moment of freezing so nothing
downstream nudges it.

### 4. Appearance

Physics is authoritative; the sprite mirrors it (§4.4).

`createOrganelleGraphics(orgObj)` bakes `orgObj.color` into a `Graphics` at
creation. Two ways to grey it:

- **Preferred:** set `o.sprite.tint = 0x8a8a8a` and reduce `alpha` slightly. One
  line, no object churn, no risk of hitbox/sprite desync. Note that the additive
  blend mode on some layers can make tint behave unexpectedly — check how it
  looks; if the tint washes out, fall back to the option below.
- **Fallback:** destroy the old sprite (using the existing
  `organellesLayer.removeChild(...); sprite.destroy();` pattern) and rebuild via
  `createOrganelleGraphics` with a grey colour. **This runs once per organelle
  per round**, so the churn is acceptable — but you must reuse the *existing*
  `o.x`, `o.y`, `o.rotation`, `o.bendY`, `o.radius` so the hitbox is unchanged.
  `createOrganelleGraphics` already respects a pre-set `bendY` (see its first
  lines) — that is exactly why. Do not let it re-randomise.

Add a brief visual cue at the moment of freezing (a one-shot alpha pulse driven
from a timestamp on the organelle) so players can see it happen. Keep it cheap —
no new display objects.

### 5. Collision — the point of the task

**Nothing to do.** Necrotic organelles remain in `organelles[]`, so
`rebuildSpatialGrid()` inserts them, `checkCollision()` sweeps against them, and
`raycast()` senses them. Confirm all three by reading, and state in the commit
message that no new collision path was added.

The only thing to verify is that the mitochondrion spine hitbox is still correct
for a frozen one — since `o.rotation` stops changing, it should be *more* stable,
not less.

### 6. Bot awareness

The bot senses them as `'organelle'` already. But a permanent wall deserves a
higher avoidance weight than a drifting one that will move out of the way. If T03
has landed, its `hazardScore` can take the hit type into account — but **do not
add that here**. Log "weight necrotic organelles higher than drifting ones" in
`docs/BACKLOG.md` and keep this task's scope clean.

---

## Files touched

`260703_Cellsnake.html` only: organelle literal in `generateMap()`, freeze block
in `gameLoop`, `updateDriftingOrganelles()` guard + one-sided pair resolution,
sprite tint/rebuild.

---

## Verification

1. Console clean.
2. **Gen 1 unaffected.** Full Gen 1 round: no organelle ever freezes.
3. **Gen 2 freezes on schedule.** `window.setGeneration(2)`, watch 90s. Roughly
   one freeze every 12s, greyed and visibly stationary.
4. **Cap holds.** Run 10 minutes at Gen 2. Necrotic count must stop at
   `floor(0.5 × 25) = 12` and never exceed it.
5. **Hitbox matches sprite.** For a frozen mitochondrion, drive along its long
   axis and its short axis. Death must occur exactly at the drawn pill outline.
   This is the desync test — do it properly, at three different frozen
   mitochondria.
6. **No new collision path.** Grep your diff: it must not contain a new
   collision function. Necrotic organelles must appear in `spatialGrid` — confirm
   by temporarily logging `gridCells` content types.
7. **Drifting organelles bounce off necrotic ones** and do not overlap them.
   Watch 2 minutes.
8. **No freeze-on-player.** Play close to organelles for 3 minutes at Gen 2 and
   confirm you are never killed by a freeze happening on top of you.
9. **Bot handles them.** A bot at Gen 2 must not repeatedly die to the same
   frozen organelle.
10. **No leak.** `worldChildren` flat over 10 minutes at Gen 2 (relevant if you
    took the sprite-rebuild fallback).
11. Regression sweep from `AGENT_CONDUCT.md` §7.6.

## Definition of done

- [ ] `o.necrotic` drives motion, appearance, and nothing else
- [ ] Zero new collision code paths
- [ ] Freeze cap and no-freeze-near-player guard both implemented
- [ ] Mitochondrion hitbox/sprite alignment verified at three instances
- [ ] Drifting/necrotic pair resolution is one-sided
- [ ] `docs/TASKS.md`: T13 → `DONE`
