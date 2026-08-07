# T38 — Make organelle necrosis actually change the game

**Track:** K (playtest design) · **Depends on:** T37 · **Risk:** medium (gameplay)

Read `docs/AGENT_CONDUCT.md`.

## The complaint

> "What does calcification of organelles do? For now it does not seem to be
> changing the gameplay too much."

## Why it feels invisible — this is correct, not imagined

Organelles were **already lethal** before T13. Read what `necrotic` actually
changes today:

- the palette (grey instead of green/pink), and
- motion: the organelle stops drifting, and pair-resolution makes it immovable.

That is all. It was lethal before and it is lethal after. So from the player's
seat, one organelle quietly turns grey and stops moving every 12 seconds — no new
threat, no new decision. T13 implemented its task file faithfully; the task file
was the thing that lacked a mechanic.

## Design goal

A necrotic organelle should change how you play the space around it. Pick **one**
clear idea, implement it well, and write the reasoning into `## Findings`.
Candidates, strongest first:

1. **They accrete.** Necrotic organelles that touch fuse into a larger rigid
   mass, so the arena gradually grows real walls rather than scattered dots.
   Reuses the existing pair-resolution, and gives Gen 2 a visible arc.
2. **They shed debris.** A necrotic organelle periodically emits a small lethal
   fragment that drifts briefly — turning a static hazard into an area you must
   time your approach to.
3. **They are destructible.** In `attack` mode (see T36) a player can shatter a
   necrotic organelle, making Gen 2 a risk/reward decision rather than pure
   attrition. Pairs naturally with T36 and T39.

Whatever you pick, keep the **visual language** honest: necrotic should read as
dead/mineralised at a glance, distinct from both healthy organelles and from
T39's growth.

## Non-negotiables

- Any change to lethality or shape goes through **both** `checkCollision` and
  `raycast` (§4.1), swept only (§4.2).
- Keep the `NECROSIS_MAX_FRAC` cap and the no-freeze-near-player guard.
- Gen 1 must be completely unaffected.

## Verification

1. Console clean.
2. Gen 1 unchanged — no necrosis at all.
3. The chosen mechanic is visible within ~60 s at Gen 2 without being told about
   it. This is the whole point — if you have to explain it, it failed.
4. Bots handle it: 2 minutes at Gen 2 without a bot repeatedly dying to the same
   spot.
5. Hitbox matches the drawing at three instances.
6. `worldChildren` flat over 10 minutes at Gen 2.
7. Regression sweep §7.6.
