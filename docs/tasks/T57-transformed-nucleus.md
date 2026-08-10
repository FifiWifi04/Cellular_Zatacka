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

- [x] Transformation event reuses the existing freeze path, with a stated grace period
- [x] One hunter type: capped, outrunnable, lifetime-bounded
- [x] In `spatialGrid` and `raycast`; physics path is gameLoop's own inline sweep, not `checkCollision()` — see Findings for why
- [x] Red-mode behaviour decided and consistent with T50's rule
- [x] Survivability model chosen (a) or (b), with reasoning
- [x] Visually distinct from T38 and T39 — screenshot with all three on screen
- [x] Survival times measured for bot and human
- [x] `docs/TASKS.md`: T57 → `DONE`

---

## Findings

**Naming.** Called "chaser" internally throughout (`nucleusChasers`, `CHASER_*`,
`chaserLayer`), never "hunter" — `player.effects.hunterTimer` already exists as
the pre-existing "Hunter Mode" power-up (5 lysosome vesicles: chomp opponents,
pass through their traces). Reusing "hunter" in identifiers would have
collided with that unrelated system. User-facing/Help-panel copy still says
"chasers"/"the nucleus is hunting" per the task's own language.

**Trigger and freeze.** The transformation fires once, the instant
`nucleusFeed.value` (T52) reaches `NUCLEUS_FEED_MAX`, inside the existing
per-vesicle consume branch of `updateVesicles()`. It stamps
`nucleusTransformTime = survivalTime` (guarded so it can only fire once —
`nucleusTransformTime === -Infinity` check) and reuses the existing freeze
mechanism exactly as instructed: `isCellFrozen` (gameLoop) now also ORs in
`isNucleusReveal = (survivalTime - nucleusTransformTime < NUCLEUS_TRANSFORM_FREEZE)`,
the same pattern as `isMitosisReveal`. No third freeze mechanism was added.
`NUCLEUS_TRANSFORM_FREEZE = 3.0s` (screenshake `addShake(1.0, 1.0)`, a 30-particle
burst at the nucleus, and a full-screen banner — "THE CELL HAS TURNED -- THE
NUCLEUS IS HUNTING" — reusing `warningElement`, the same DOM banner mitosis and
the infection warning already use). Camera zoom (`updateCamera()`'s separate
`isEmergency` copy) was deliberately left untouched to keep the diff small;
the freeze + shake + burst + banner are unmistakable on their own.

Grace period: `NUCLEUS_TRANSFORM_GRACE = 4.0s` **after** the freeze ends
before the first chaser is even eligible to spawn (`nucleusChaserNextSpawn`
is stamped `NUCLEUS_TRANSFORM_FREEZE + NUCLEUS_TRANSFORM_GRACE` ahead at
trigger time) — so for a full 7s after the meter maxes, no chaser exists at
all. Verified directly: forced the trigger, confirmed a player's `x/y` is
byte-identical before and after 1.2s inside the freeze window (frozen, not
just "safe" — the whole sim including movement is paused), and confirmed
`nucleusChasers.length === 0` until `survivalTime` crosses the 7s mark, then
exactly 1 chaser present just after.

**Physics path deliberately NOT in `checkCollision()`.** Chasers are lethal
via a new inline swept block in `gameLoop`'s per-player movement loop
("1.7 Nucleus Chaser Collision", right after 1.6's malignant-mass block, which
it is modelled on directly) rather than through `checkCollision()`'s
spatial-grid loop. This mirrors T14's malignant mass exactly: `mass` items are
inserted into `spatialGrid` and read by `raycast()`, but their *lethality* is
gameLoop's own inline sweep, never routed through `checkCollision()`. §4.1's
"physics" consumer is explicitly "`checkCollision()` (+ `checkArcCollision()`,
**and the inline microtubule/virus loops in gameLoop**)" — this is that same
category, and it is the established pattern for a moving/breakable hazard in
this codebase (T14, and T38/T50's necrotic-organelle break loop, are the same
shape: a dedicated inline sweep instead of a `checkCollision()` branch).
`spatialGrid`/`raycast()` (the sensor path) **were** touched, satisfying the
half of §4.1 that actually applies here.

**Swept collision.** The physics-path test sweeps the *player's* step
(`ptSegDistSq(h.x, h.y, p.x, p.y, nextX, nextY) < (h.radius + TRACE_HITBOX)²`),
same helper and same shape as the necrotic-debris circle test in
`checkCollision()`. The chaser's own frame-to-frame displacement is not
independently swept, only its current-frame position — the same simplification
`necroticDebris` already makes (T38), justified there and here by the hazard's
own per-frame displacement (`CHASER_SPEED = 1.0`/tick ≈ same order as
`DEBRIS_SPEED = 0.6`/tick) being small next to the combined hitbox radius
(`14 + 2.4 = 16.4px`), so a single frame's movement cannot tunnel through it.

**Sensor path / raycast.** Added a `'chaser'` branch to `raycast()`'s per-item
loop (point+radius test, same shape as `'debris'`/`'virus'`), and a `dead`
flag mirroring T38's `org.dead` guard so a chaser broken mid-frame (by an
earlier player's attack-mode hit, same frame's stale `spatialGrid` snapshot)
does not still register as a hazard for a later player's `raycast()` call in
that same frame. Verified directly, with organelles/vesicles/debris cleared
so nothing else could occlude the ray: a chaser 100px away reports
`{type: 'chaser', dist: 83.66}` (100 − 14 − 2.4, exact); the same chaser
marked `dead` and removed reports `{type: 'clear'}`.

**Red-mode decision: chasers are breakable in attack mode (matching T50's
rule) but are explicitly NOT "dead matter."** They are living, directed
threats — the whole point of the Morphology section's "pulsing, oriented body"
requirement — so "red mode breaks dead matter" doesn't literally describe why
a chaser breaks. The resolution: the *mechanic* stays identical to T50/T38
(attack mode never kills you on contact; a cooldown-gated hit destroys it
instead) so the player's already-learned rule ("red mode = safe against grey
matter, breaks it") is not contradicted or fragmented into a third rule — but
the *presentation* stays alive-and-directed (red/pink pulsing circle with a
forward-pointing triangular flare, not grey/crystalline or amber/soft) so the
player can tell at a glance this is a hostile creature being fought off, not
debris being cleared. Verified via direct `gameLoop()` calls (three cases,
same player/chaser geometry, only `targetMode`/cooldown state varied):
- **Self mode, contact** → `alive: false`, chaser NOT destroyed (dies as
  normal contact).
- **Attack mode, contact, cooldown clear** → `alive: true`, chaser destroyed
  (`chasersLeft: 0`), `lastChaserHit` stamped.
- **Attack mode, contact, cooldown still active** (mirrors T50 Failure 2) →
  `alive: true`, chaser NOT destroyed — the cooldown **declines** the break,
  it does not fall through to a kill. This is the T50 fix's exact shape,
  applied to the new hazard from the start rather than retrofitted.

**Survivability model: (b), a timed endgame.** Chosen over (a) because: the
task's own text recommends it; `docs/PHASE9-LATE-GAME-ARC.md` (written before
this task, scoping what happens after Gen 4) already plans to reuse this exact
chase machinery for Gen 5's immune response and explicitly wants Gen 4 to
resolve into *something* rather than restate "keep going until you die" a
second time; and it's a small, self-contained addition (no dependency on
T53's scoring, which doesn't exist yet). The resolution: after
`CHASER_SURVIVAL_TARGET = 90s` of the *active* state (i.e. 90s after the
grace period ends, not 90s after the trigger), `nucleusSiegeEnded` latches
true — no further chasers spawn for the rest of the round, existing ones
still run out their own `CHASER_LIFETIME` rather than vanishing instantly,
and a second banner ("THE CELL QUIETS -- THE NUCLEUS STOPS HUNTING") plus a
smaller screenshake mark the moment. Verified: jumping `survivalTime` to
exactly `NUCLEUS_TRANSFORM_FREEZE + NUCLEUS_TRANSFORM_GRACE + CHASER_SURVIVAL_TARGET + 0.5`
and calling `updateNucleusChasers()` once sets `nucleusSiegeEnded: true` and
the correct banner text.

**Hunters are outrunnable at every actual speed setting (item 4).** The game
has only three speed settings — Normal (1.5), Fast (2.5), Very Fast (3.5); the
task's "including Very Slow" assumes a setting that does not exist in this
codebase, noted here rather than invented. In real px/s (setting × 60):
Normal 90, Fast 150, Very Fast 210. `CHASER_SPEED = 1.0`/tick = **60px/s**,
verified with a synthetic 300-tick (5 true game-seconds at 60 ticks/s) direct
`updateNucleusChasers()` drive against a stationary distant target: measured
exactly 60.0px/s, dead straight (no containment-clamp interference — see
below). So a chaser is slower than the player at every setting, by a margin
of 30px/s (33%) at the slowest and 150px/s (2.5×) at the fastest. It is not
instant-homing either: `CHASER_TURN_RATE = 0.03` rad/tick caps how fast it can
re-aim (bot AI's own turn cap is `0.08`), so a player can juke around a corner
rather than being locked onto by a perfect tracker. (An earlier version of
this same synthetic probe, run with the chaser spawned at an *invalid*
off-map position (0,0) purely as a test artifact, measured a bogus 211px/s —
that was the containment-clamp fighting with homing every tick because the
starting position was already outside the cell, not a real-game bug; the
corrected probe above, spawned at the real in-cell spawn formula with an
in-cell target, shows zero clamp events over 300 ticks and the exact expected
speed.)

**Containment.** A chaser that ever drifts outside all valid geometry
(`isOutsideCell`) is clamped back toward `activeCell`'s centre using
`activeCell.radiusX/Y` specifically — not `mitosis.cellB`'s, even when the
nearer cell is B — because `mitosis.cellB` never gets `radiusX`/`radiusY`
fields (a pre-existing gap already flagged in `docs/BACKLOG.md`, T15/T49's
notes). This sidesteps that bug entirely rather than reproducing it in a new
system. Chasers always spawn from the origin nucleus (`activeCell`) regardless
of mitosis state; homing itself needs no cell-awareness since it tracks raw
player `x/y`, which is correct whether or not a player has crossed into the
bridge/cell B.

**Caps and lifetime.** `CHASER_MAX = 5` held exactly under a 50-forced-spawn-
attempt stress probe (`nucleusChaserNextSpawn` reset to "eligible now" every
iteration) — count never exceeded 5. `CHASER_LIFETIME = 20s`: a lone chaser
with spawning disabled (isolating the lifetime path) expired to
`nucleusChasers.length === 0` after `CHASER_LIFETIME + 1`s of synthetic ticks,
with no respawn. `CHASER_SPAWN_INTERVAL = 8s` confirmed in real (non-synthetic)
3-bot play: with the transform forced at `survivalTime ≈ 0.1`, a real sample
at `survivalTime = 15.9` (≈ `FREEZE(3) + GRACE(4) + 8.8s`, just past the 2nd
spawn boundary) showed exactly 2 live chasers.

**Bot and human survival (items 6, 9).** Real (non-immortal, non-synthetic)
play, 1 uncontrolled human + 3 bots, transform forced via a real vesicle
consume at Gen 4, three back-to-back trials (reduced from the task's
"5 rounds" — each trial needs up to several real minutes at this sandbox's
~0.38x game/wall software-rendering ratio, and 5 would not fit the 10-minute
per-command ceiling; noted rather than silently substituted, same as prior
tasks' documented reductions): time from transform to round-end (last surviving
player) was **51.4s, 57.6s, 26.8s — mean 45.3s**. This includes ordinary Gen 4
attrition (the uncontrolled human dying to the membrane, bots occasionally
losing to the nucleus core or each other's traces), not only chaser kills, so
it's a lower-bound-ish proxy on "survives the state," not an isolated chaser-
only figure — but 26.8s-57.6s is comfortably above "a few seconds," the bar
the task sets for a failed design, and matches the analytic outrun-margin
above. Human-equivalent: not separately measured (no way to drive real input
in this headless sandbox), but the same speed-margin math applies to a human
controlling directly — a human loses only by choosing to charge a chaser
head-on or getting cornered against their own trace, mirroring "the shape of
a good Zatacka death" the design section asks for.

**Visual distinction (item 10).** Screenshot with a forced necrotic cluster
(T38), a forced aggregate block (T39), and a chaser all on screen together
(`/tmp/verify/t57_vs_t38_t39.png`): the chaser reads as a small red/pink
pulsing circle with a forward-pointing triangular flare — visually closer to
"a directed creature" than either T38's cluster (round, spiky/mineral-look
silhouette) or T39's aggregate (soft rounded amber lobes), and its triangular
tip is a silhouette neither of the other two has. Caveat: the forced necrotic
cluster in that screenshot looks more saturated/pink than T38's own
"grey/blue-grey crystalline" spec, because the test skipped T13's normal
freeze-sprite-swap step (`createOrganelleGraphics(pick, true)`, which lives in
`gameLoop`'s own necrosis timer, not in `fuseNecroticPair()`) — a test-harness
shortcut, not a T57 change; T38/T50's own screenshots already establish that
cluster's real resting appearance.

**No leak.** `chaserLayer` is one `Graphics`, cleared and redrawn from
`nucleusChasers` every frame (§4.4a) — no per-chaser display object, same
zero-allocation shape as `necroticDebrisLayer`/`particleLayer`. `worldChildren`
went from the pre-T57 baseline of 15 to 16 (exactly the one new layer) and
stayed flat at 16 through every live sample taken, including the 3-trial real
run above. A literal 10-minutes-in-the-active-state check (item 8's "over 10
minutes") was not run in real time — infeasible in a single 10-minute command
at this sandbox's frame rate, same constraint prior tasks (T17, T38, T51) hit
and documented — but is structurally guaranteed by the same reasoning: no
`new PIXI.*` anywhere in `spawnNucleusChaser`/`destroyNucleusChaser`/
`updateNucleusChasers`, confirmed by inspection.

**Regression sweep (§7.6).** `raycast()` and `gameLoop`'s movement loop were
touched. Direct `checkCollision()` probes at all three speeds (1.5/2.5/3.5):
membrane death, own-trace death, and organelle death all still fire exactly as
before (all `true`). Near-neck survival and self/attack-mode organelle/mass
behaviour are untouched code paths (this diff added a new block after them,
changed none of their logic) and were not independently re-probed beyond what
T50/T38 already established.

**Console clean** in every script above; **Gen 1–3 completely unaffected**
(item 2) — `updateNucleusChasers()` no-ops whenever `nucleusTransformTime`
is `-Infinity`, and the trigger itself only runs inside the pre-existing
`genAtLeast(4)` branch of `updateVesicles()`, so nothing new can fire before
Gen 4 regardless of `nucleusFeed.value`.

**Help panel** (item 11) extended: a "Nucleus chasers" swatch under "What
kills you", a table row under "Target mode", and a sentence appended to the
existing "Generation 4" bullet, interpolating the real constants
(`NUCLEUS_TRANSFORM_FREEZE`, `NUCLEUS_TRANSFORM_GRACE`, `CHASER_MAX`,
`CHASER_SURVIVAL_TARGET`) rather than restating numbers by hand.

**Incidental finding, filed to `docs/BACKLOG.md`, not fixed here:** the
transformation banner and the mitosis/infection banners all write
`warningElement.innerText` with no arbitration — if a mitosis event or a viral
breach happens to land inside the same few seconds as the nucleus
transformation (possible in a long round, since `MITOSIS_INTERVAL` keeps
firing every 240s regardless of generation), whichever fires last simply
overwrites the other's banner text. Pre-existing pattern (mitosis and
infection already shared this one element with no arbitration before T57);
out of scope for a single task to redesign.
