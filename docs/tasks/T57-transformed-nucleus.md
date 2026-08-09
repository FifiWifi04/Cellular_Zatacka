# T57 — When the nucleus is full: the cell turns on the microtubule

**Track:** K · **Depends on:** T52 · **Risk:** high (new hostile entity class) · **Est. diff:** ~220 lines

Owner design, 2026-08-09: *"by consuming different vesicles it grows and becomes
cancer cell with a lot of things trying to 'kill' the microtubule."*

[T52](T52-gen4-nucleus-feeding.md) builds the race — the nucleus eats, a bar
fills, the player collects to slow it. This is what happens when the bar fills.

**Do not start this before T52 has been played.** The whole feel of this state
depends on how long the race takes and how it accelerates, and those numbers do
not exist until T52 is tuned.

---

## What it is

The nucleus completes its transformation and the cell stops being a neutral arena
that happens to contain hazards. It starts actively hunting the player.

Everything before this is **static or drifting** — organelles drift, clusters sit,
the aggregate grows in place, debris expires. Nothing in this game has ever
*chased* the player. That is what makes this a real ending state rather than one
more hazard, and it is also why it is the highest-risk task on the board.

## Design

### 1. The transformation is an event, not a fade

It must be unmistakable, and it must give the player a moment to react before
anything can kill them:

- Freeze or slow the sim briefly, the way the existing `isCellFrozen` path
  already does for the infection warning and the mitosis reveal — **reuse that
  path**, do not add a third freeze mechanism.
- Screenshake (T16), a burst (T17, pooled), a palette shift on the nucleus.
- A clear grace period, stated as a constant, before the first hunter is lethal.
  Killing the player during the cutscene would be the worst possible first
  impression of this feature.

### 2. The hunters

The "lot of things trying to kill the microtubule". One new entity type — resist
making three.

- Spawn from the nucleus, on a timer, capped hard (`HUNTER_MAX`).
- **Move toward the player's head**, but slowly enough to be outrun and steered
  around. They are pressure, not a death sentence: the player should die to being
  cornered between a hunter and their own trace, which is the shape of a good
  Zatacka death.
- Lethal on contact and therefore **in `rebuildSpatialGrid()`, `checkCollision()`
  AND `raycast()`** (§4.1). A lethal thing the bot cannot see is the single most
  repeated mistake in this codebase, and a *homing* one the bot cannot see will
  look absurd.
- **Breakable in red mode**, one per hit with a cooldown, consistent with T50's
  unified rule — after T50, "red mode breaks dead matter" is a rule the player
  has learned, and this must not contradict it. Decide and state whether a
  hunter is "dead matter"; if it is not, it must look *alive* so the player can
  tell at a glance.
- Give them a lifetime, or the arena saturates and the state stops being playable
  rather than becoming hard.

### 3. Is the state survivable?

Decide, and say why in `## Findings`:

- **(a) Survivable indefinitely, just very hard.** Consistent with the rest of the
  game — every generation is "keep going until you die".
- **(b) A timed endgame** — survive N seconds in this state and something
  resolves (a final mitosis, an escape). Gives the run a shape and an ending
  that is not just death. **Recommended**, and it pairs naturally with T53's
  scoring, where reaching and surviving the transformation should be worth the
  most points in the game.

Do not build both.

### 4. Morphology

It must not look like the protein aggregate (T39, soft amber lobes) or a necrotic
cluster (T38, grey crystalline facets). Those two are already a pair the player
has to tell apart; a third amorphous mass would make the screen unreadable.

Hunters should read as **alive and directed** — motion is the strongest cue
available, so lean on it: a pulsing, oriented body that visibly points where it
is going. One persistent `Graphics` redrawn from state (§4.4a), never one per
hunter per frame.

## Verification

1. Console clean.
2. **Generations 1–3 and pre-transformation Gen 4 completely unaffected.**
3. The transformation event fires exactly once per round, at the meter's max, and
   the grace period is respected — a player parked next to the nucleus survives it.
4. **Hunters are outrunnable** — measure hunter speed against player speed at
   every speed setting including Very Slow. If they catch a fleeing player in the
   open at any setting, they are too fast.
5. **Both collision paths** (§4.1): head-on at Very Fast under 4× fuzzer dilation
   registers with no tunnelling, and `raycast()` reports them.
6. **The bot survives the state** for a measurable time — 5 rounds, report mean
   survival after transformation. A bot that dies in 2 seconds every time means
   they cannot be seen or cannot be avoided.
7. Red-mode interaction behaves as decided, with the cooldown respected.
8. Caps hold: `HUNTER_MAX` never exceeded over 10 minutes in the state.
9. **Playable, not hopeless.** Report human-equivalent survival time in the state
   at each speed setting. If it is under a few seconds the design failed.
10. `worldChildren` flat over 10 minutes in the state; destroyed hunters release
    their sprites.
11. Help panel updated.
12. Regression sweep §7.6.

## Definition of done

- [ ] Transformation event reuses the existing freeze path, with a stated grace period
- [ ] One hunter type: capped, outrunnable, lifetime-bounded
- [ ] In `spatialGrid`, `checkCollision` **and** `raycast`
- [ ] Red-mode behaviour decided and consistent with T50's rule
- [ ] Survivability model chosen (a) or (b), with reasoning
- [ ] Visually distinct from T38 and T39 — screenshot with all three on screen
- [ ] Survival times measured for bot and human
- [ ] `docs/TASKS.md`: T57 → `DONE`

---

## Findings

*(Survivability model and why; hunter speed vs player speed at each setting; bot
and human survival times; the red-mode decision.)*
