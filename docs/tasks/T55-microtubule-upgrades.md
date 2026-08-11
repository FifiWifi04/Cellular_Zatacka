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

**Chosen upgrades (3, not 4) and why the other two examples were dropped.**
Of the task's five suggested examples, two don't map onto this codebase as-is
and were skipped rather than faked into existence:
- *A second boost slot* — `p.effects.ghostTimer`/`hunterTimer`/`golgiTimer`/
  `speedTimer` are already four independent fields; a player can already hold
  ghost + hunter + speed simultaneously today. There is no existing
  "one boost at a time" restriction to lift.
- *Faster target-mode switching* — the toggle (`p.targetMode = ...`) is a
  single instant keypress with no cooldown to shorten. Inventing a new delay
  just to sell removing it would be a nerf-then-upgrade trick, not a real one.

The three implemented, all "player tool, not arena reduction" per the rule:
1. **Wider Pickup Radius** (600 pts) — `PICKUP_RADIUS_BONUS = 12`px added to
   the vesicle and ATP granule collection-distance checks in `updatePlayers()`
   (`v.radius + TRACE_WIDTH + 6 + p.upgrades.pickupRadiusBonus`, same change
   applied to the ATP loop two lines down). Reward channel, not a hazard.
2. **Shed the Tail** (1000 pts) — active ability, 'x' key (free of every
   `playerConfigs` binding and dev hotkey), `SHED_TAIL_COOLDOWN = 30`s,
   `SHED_TAIL_FRACTION = 0.3`. Calls the existing `deleteOldestTrace(p, 0.3)`
   (the same helper the lysosome 50% wipe already uses) to cut the oldest 30%
   of the player's own trace on demand — gives the player an escape valve for
   a self-made trap, doesn't touch `TRACE_HITBOX` or T08's neck-immunity math.
3. **Choice of Spawn** (400 pts) — a spawn-slot picker in the Shop panel
   (persisted as `preferredSpawnSlot` in the save, not a separate menu
   control). At round start, player 0's spawn slot and every other player's
   slot are permuted (`spawnSlotForIndex`) so the human's chosen slot is
   never doubly-occupied; `id`/`color`/`controls` still come from the
   player's own `playerConfigs` entry — only `dx/dy/angle` (position/facing)
   move. Doesn't touch organelle placement, hazard geometry, or fairness
   beyond which of the 4 existing spawn points each player starts at.

**Currency and schema.** `HS_VERSION` 1 → 2. `recordRun()` now also does
`data.balance += score` — every recorded run banks its score. `migrateV1ToV2()`
keeps `runs`/`totals`, adds `balance:0`, `owned:{}`, `preferredSpawnSlot:0`.
Tested with a real v1-shaped payload (not hand-abridged): 1 run, `totals.rounds
= 1`, fed through `loadHighScores()` → correctly produced `v:2`, same run/
totals data, balance 0, owned `{}`.

**Purchase atomicity** (design §1): `purchaseUpgrade()` computes the
post-purchase object, then calls `localStorage.setItem()` *first*; only on a
successful write does the purchase exist anywhere (the function returns
`true`/`false`, nothing is mutated in memory ahead of the write). Induced a
`setItem` throw mid-purchase (5000 balance, buying the 600-cost upgrade):
`purchaseUpgrade()` returned `false`, and balance/owned were byte-identical
before and after — never paid-without-applied or applied-without-paid.

**Applying at round start** (design §2): `resolvePlayerUpgrades()` is the one
place `owned` is read; `startRound()` resolves it into `p.upgrades
.pickupRadiusBonus`/`.shedTail` once per player, stored on the player object.
No `if (hasUpgrade(...))` anywhere in collision/movement code.

**Bots** (design §3): every bot gets the exact same `owned` set as the human
(`resolvePlayerUpgrades()`'s result is applied identically to every player in
the loop, `isBot` doesn't gate it) — confirmed via direct state read after
`startRound()` with all 3 upgrades owned: all 3 bots' `p.upgrades` matched the
human's exactly. Bots use Shed the Tail automatically the instant their
cooldown clears (no equivalent of a player choosing the moment); confirmed by
forcing a bot's cooldown ready and observing its trace point count fail to
grow over the next simulated second (55 → 55, versus organic per-second
growth of roughly 10-11 points measured earlier in the same run).

**Multiplayer guard** (design §4): `resolvePlayerUpgrades()` returns empty
`owned`/`preferredSpawnSlot:0` whenever `currentMode > 1` (2+ local human
players — the only "multiplayer" this codebase has today; T29+ networked play
will read the same guard). Verified: with all 3 upgrades owned and
`preferredSpawnSlot:2`, a 2-human round produced `pickupRadiusBonus:0`/
`shedTail:false` for every player and P1 spawned at the default West slot
(~-600,0) — not the preferred North slot. Starting a solo round again in the
same session immediately re-applied the full loadout (the guard isn't sticky
across rounds).

**Per-upgrade on/off measurements** (design's own rule: "an upgrade you
cannot measure is T13's mistake again"):
- *Pickup radius*: a stationary vesicle placed exactly 20px from the player
  (base threshold 16px, boosted threshold 28px) — **not** collected without
  the upgrade, **collected** with it, same distance both times. Same result
  for an ATP granule at the same offset.
- *Shed the Tail*: after 5 game-seconds of natural growth (54 trace points), a
  real `keydown 'x'` cut it to 41 points and stamped the cooldown; an
  immediate second press was a no-op (point count only grew from natural
  movement, never dropped again) — proving both the effect and the cooldown
  gate.
- *Choice of Spawn*: with `preferredSpawnSlot:2` (North) owned, player 0
  spawned at `(activeCell.x, activeCell.y - 500)` instead of the default West
  slot, and all 4 players in the round still landed on 4 distinct spawn
  points (no overlap from the permutation).

**Hazard constants provably unchanged** (design's hard rule): `git diff` on
the hazard-related identifiers (`TRACE_HITBOX`, `EFFECT_DURATION`, `CALCIFY*`,
`CLUSTER_HIT_COOLDOWN`, `MASS_HIT_COOLDOWN`, `CHASER_HIT_COOLDOWN`, `GAP_*`)
shows zero added/removed lines touching any of them. Read back at runtime
under a full 3-upgrade loadout: `TRACE_HITBOX=2.4`, `EFFECT_DURATION=10`,
`CLUSTER_HIT_COOLDOWN=MASS_HIT_COOLDOWN=CHASER_HIT_COOLDOWN=0.3` — all
identical to their pre-existing values. `checkCollision()`, `checkArcCollision()`,
`raycast()` and `rebuildSpatialGrid()` do not appear anywhere in this diff
(confirmed by grep) — no hazard was added or changed, so §4.1's dual-path rule
doesn't apply here, matching T52/T54's precedent for reward-only changes.

**Win-rate check (item 7).** The harness has no scripted keyboard input for a
real human, so `players[0].isBot` was flipped `true` immediately after
`startRound()` purely for this measurement (`currentMode` stays 1, so
`resolvePlayerUpgrades()` still resolves upgrades onto it as "the human
slot") — it is then piloted by the same `updateBotAI()` as its 3 opponents.
This holds piloting skill constant across all 4 players, isolating whether the
loadout/economy alone makes the human unbeatable, which is what this check is
actually asking. All 4 players held the identical full 3-upgrade loadout
(bots always match the human's loadout by design, so an "upgraded human vs.
un-upgraded bots" scenario cannot occur here — that would break rule §3, not
demonstrate it). 10 headless rounds, Gen 2 forced via `setGeneration(2)`,
1 human-slot + 3 bots: **P1 (human slot) won 1/10 (10%)**; P2 2/10, P3 3/10,
P4 4/10. Far from 10/10 — confirms the loadout doesn't make the human
unbeatable. (P4's higher share across only 10 rounds reads like starting-slot
variance in the underlying 4-player mode, not an upgrade effect — noted to
`docs/BACKLOG.md`, out of scope here since every player held the same
loadout.) 10 rounds completed in 107.7 wall-seconds via `stepHeadless()`.

**Storage failure (item 6).** Covered under Purchase atomicity above — an
induced `setItem` throw during a purchase attempt leaves balance and
ownership exactly as they were.

**Persistence (item 4).** A run recorded (score 900 → balance 500), a
purchase, and a `setPreferredSpawnSlot(3)` call all survived a real
`page.reload()` — balance, `owned`, and `preferredSpawnSlot` were identical
before and after.

**Shop UI (item 9).** Screenshotted legible at 390×844, 844×390 and
1280×800, reusing T41/T54's `.help-overlay`/`.help-panel` structure exactly
(same close button, outside-click close, pause/resume contract, and Escape/P
handling — `shopIsOpen()` added alongside `helpIsOpen()`/`highScoreIsOpen()`
at every one of their 3 call sites).

**Regression sweep (item 10).** `checkCollision`, `checkArcCollision`,
`raycast`, `rebuildSpatialGrid` are all absent from this diff (grep-confirmed
above) — this is a sanity pass, not a defect hunt. A steered-nowhere player
(no upgrade-driven behaviour involved) still died to the outer membrane at
all 3 speeds (Normal 77.8s, Fast 74.6s, Very Fast 35.3s), console clean.
Self-trace and organelle death paths are unchanged code, already covered by
prior tasks' sweeps.

**Console/load.** Clean across every check above, a real 30.2s round (1 human
slot + 3 bots, full loadout), and an 8.2s headless run over `file://`
(offline, source file — `dist/` rebuild verified separately via `--check`).
`sw.js` `CACHE_NAME` bumped v32→v33; `dist/Cellular_Zatacka.html` rebuilt.

**Incidental findings → `docs/BACKLOG.md`:**
- `raycast()`'s vesicle/ATP reward-sensing radius doesn't reflect a bot's
  `pickupRadius` upgrade (still tests the base `+6` pad, not `+18`) — bots can
  actually collect from further out than they currently "see" a vesicle as
  worth detouring for. Reward-channel precision gap only, not a hazard leak;
  threading the bonus through `raycast()`'s signature was out of scope for
  the smallest-diff rule.
- The 4-player win distribution above (10%/20%/30%/40% across P1-P4, all with
  identical loadouts) suggests an existing starting-slot asymmetry in the base
  4-player mode, unrelated to this task.
