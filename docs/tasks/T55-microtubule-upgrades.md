# T55 — Spend points on microtubule upgrades

**Track:** L (Phase 8) · **Depends on:** T54 · **Risk:** high (changes game balance permanently) · **Est. diff:** ~180 lines

Read [`docs/PHASE8-META-PROGRESSION.md`](../PHASE8-META-PROGRESSION.md) — in
particular the section on upgrades, which sets the one rule this task must not
break.

Owner request: *"get points so they can buy 'improvements' for their microtubule
to increase its survivability."*

---

## The rule

> **Upgrades change the player's tools. They do not change the hazards' rules.**

Every hazard in this game was made meaningful by a specific task, and the obvious
upgrades quietly undo them:

| Tempting upgrade | What it undoes |
|---|---|
| Thinner trace hitbox | T08's neck-immunity tuning |
| Longer ghost | organelle placement pressure |
| Slower calcification | T51, which is already the counterplay to calcification |
| Bigger red-mode break radius | T50's break cooldown |

None of those. Prefer upgrades that give the player **more to do**, not the arena
less:

- a second boost slot (hold two effects at once)
- faster target-mode switching
- a start-of-round choice of spawn position
- one "shed the tail" ability, on a long cooldown
- a wider vesicle pickup radius (a tool, not a hazard nerf)

Pick a small set — **three or four** — implement them properly, and leave room.
A long list of weak upgrades is worse than three that change how a round plays.

## Design

### 1. Currency

Points come from T53's score, banked across runs by T54. Store the balance in the
same versioned payload — **bump the schema version and write the migration**,
which is the reason T54 was told to version from day one.

Spending must be atomic against the storage failures T54 enumerated: a purchase
that succeeds in memory and fails to persist must not leave the player paid-up
and un-upgraded, or vice versa. Decide the order (write first, then apply) and
say so.

### 2. Applying an upgrade

Owned upgrades are read where the player's per-round state is built, next to
`p.effects` — **one place**, so that a round always starts from a single,
inspectable description of what this player can do. Do not scatter
`if (hasUpgrade(...))` through the movement and collision paths; resolve to
plain numbers on the player object once, at round start, and let the existing
code read those numbers as it already does.

### 3. Bots

Bots must be able to hold the same upgrades, and single-player rounds should give
them a comparable loadout to the human's. Otherwise every purchase quietly makes
the game easier and the difficulty curve inverts as the player progresses. State
in `## Findings` how bot loadout is chosen.

### 4. Multiplayer

Per the phase doc: **upgrades do not apply in multiplayer.** Write that down in
the code as a guarded check, not just in the design doc, so T30's state sync
never has to carry per-player capability differences.

### 5. The shop

Reachable from the main menu, same overlay structure as T41/T54. Each upgrade
shows cost, what it does in one plain sentence, and whether it is owned. No
currency purchase, no ads, no dark patterns — this is a local single-player
progression.

## Verification

1. Console clean.
2. Each upgrade demonstrably changes play — for each one, a measurement showing
   the difference with it on and off. An upgrade you cannot measure is T13's
   mistake again.
3. **Hazards are provably unchanged.** For each hazard touched by the table above,
   show the constant is identical with a full upgrade loadout. This is the test
   that enforces the rule.
4. Purchase persists across reload; balance is correct after several purchases.
5. **Migration works**: a T54-era save (v1) loads, keeps its history, and gains a
   zero balance. Test with a real v1 payload, not a hand-written one.
6. Storage failure during a purchase leaves a consistent state — induce it and
   show which way it fails.
7. Bots carry a comparable loadout; 4-player round at Gen 2 with the human fully
   upgraded still ends with the human losing sometimes. Report the win rate over
   10 rounds — if it is 10/10, the upgrades are too strong.
8. Multiplayer guard holds.
9. Shop renders at 390×844, 844×390, 1280×800.
10. Regression sweep §7.6.

## Definition of done

- [ ] 3–4 upgrades, each measured on and off
- [ ] Hazard constants proven unchanged under a full loadout
- [ ] Versioned save migration from T54's schema, tested with a real v1 payload
- [ ] Bots carry comparable loadouts; win rate reported
- [ ] Upgrades guarded off in multiplayer
- [ ] `docs/TASKS.md`: T55 → `DONE`

---

## Findings

*(The chosen upgrades and why; per-upgrade measurements; the hazard-constants
proof; migration test; bot loadout rule and the 10-round win rate.)*
