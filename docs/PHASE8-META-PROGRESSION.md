# Phase 8 — Scoring, statistics and microtubule upgrades

Owner request, 2026-08-09:

> *"In the long term it would be nice if players can see their high-scores with
> different statistics not only time they have survived and get points so they
> can buy 'improvements' for their microtubule to increase its survivability."*

This is the game's first **meta**-layer: the first thing that persists between
rounds. Everything shipped so far is one round long. That makes it a different
class of change from Tracks J and K, and worth scoping before any of it is built.

---

## The three pieces, and why they are separate tasks

| | Task | What it is | Why it can ship alone |
|---|---|---|---|
| 1 | **T53** | Count what happens in a round; turn it into a score | An end-of-round stats card is useful on its own, and nothing else can be built without the counters |
| 2 | **T54** | Remember runs across sessions; show a high-score table | Gives the score somewhere to live; needs T53's numbers, nothing more |
| 3 | **T55** | Spend a persistent currency on microtubule upgrades | Changes the balance of the game itself, so it goes last, on top of two proven layers |

Building them in one pass would mean tuning an economy against a score that has
never been played with. Build 1, play it, then 2, then 3.

## What "score" should mean

Survival time is currently the only number, and it rewards the safest possible
play — hug the wall, never take a vesicle. A score should reward the things the
game is *about*, so at minimum it counts:

- time survived (kept — it is the spine)
- generations reached, weighted heavily: reaching Gen 3 is the real achievement
- vesicles collected, by type
- necrotic organelles and aggregate blocks broken in red mode
- mitosis events completed
- distance travelled, as a proxy for not turtling

Deliberately **not** counted: kills. This is a survival game with bots standing
in for players; scoring kills would push the design toward deathmatch, which is
Phase 7's territory, not this one.

## Persistence

`localStorage`, single-origin, no account, no network. It must degrade
gracefully — private browsing and a full quota both throw, and the game must
keep playing when they do. This is the same constraint the PWA (T27) already
works under.

A stored schema needs a version field from day one. The upgrade layer will want
to change it, and a save that cannot be migrated is a save that gets wiped.

## Upgrades — the part to be careful with

"Improvements to the microtubule to increase survivability" is the fun part and
the dangerous one. Every candidate upgrade is a **direct nerf to the hazards the
last twenty tasks were spent making meaningful**:

- a thinner hitbox undoes T08's neck tuning
- a longer ghost undoes organelle placement pressure
- slower calcification collides head-on with T51, which is already the
  counterplay to calcification
- a wider red-mode break radius undoes T50's careful cooldown

So T55 carries a hard rule: **upgrades change the player's tools, not the
hazards' rules.** Prefer things that give the player more agency (a second boost
slot, a shorter target-mode switch delay, one respawn of the trace behind you)
over things that reduce what the arena does. And the bots must be able to use
whatever the player can, or single-player difficulty drifts every time someone
buys something.

## Interaction with Phase 7 (multiplayer)

Persistent upgrades and host-authoritative netcode do not mix casually: if
player A has bought a smaller hitbox, the host has to know that, and it has to be
part of the state sync in T30. Decide before T55 whether upgrades apply in
multiplayer at all. Recommended: **no** — upgrades are a single-player
progression, multiplayer is symmetric. It is one line in the design and saves a
whole class of desync and fairness problems.

## Order

T53 → T54 → T55, after Track J's defects and after T22 (the sim/render split),
which makes the counters much easier to place correctly.
