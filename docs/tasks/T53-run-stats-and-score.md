# T53 — Count what happened in a round, and score it

**Track:** L (Phase 8) · **Depends on:** — · **Risk:** low · **Est. diff:** ~130 lines

Read [`docs/PHASE8-META-PROGRESSION.md`](../PHASE8-META-PROGRESSION.md) first —
it explains why this is one of three tasks and what score is meant to reward.

Today the end of a round says `Game Over! Time: 58.0s · Gen 3` and nothing else.
This task adds the counters and the end-of-round card. It stores nothing across
sessions — that is T54.

---

## Design

### 1. One stats object per player per round

```
p.stats = { vesicles: {speed: 0, ghost: 0, golgi: 0, ...}, clusterBreaks: 0,
            massBreaks: 0, mitosisEvents: 0, distance: 0, maxGeneration: 1 }
```

Reset it where the rest of the per-round player state is reset, in the same place
`p.effects` is built — not in a second initialiser that will drift from it.

**Increment at the existing event sites**, never by re-deriving after the fact:
the vesicle pickup switch, `breakClusterMember()`, the T14 mass shatter branch,
the mitosis completion, and the movement step for distance. Each is one line. If
you find yourself scanning arrays to reconstruct a count, you are in the wrong
place.

### 2. Score formula — one function, named constants

```js
const SCORE = { perSecond: …, perGeneration: …, perVesicle: …, perBreak: …, per100px: … };
function scoreRun(stats, survivalTime) { … }
```

Generations must dominate: reaching Gen 3 should beat a long, timid Gen 1 round.
State the weights and the reasoning in `## Findings`, and show three worked
examples — a timid Gen 1 run, an aggressive Gen 2 run, a long Gen 3 run — with
the resulting scores. If the timid run wins, the weights are wrong.

### 3. End-of-round card

Extend the existing game-over element rather than adding a new overlay. Per
surviving/dead player: score, time, generation reached, vesicles by type, breaks,
mitosis events. Keep it readable at 390px wide (T24's clamp pattern) and inside
`90dvh` — it must not become a second thing that will not fit on a phone.

The card must not block restarting. Whatever key/tap restarts a round today must
still restart it with the card up.

### 4. Bots count too

Bots get the same stats object and appear on the card. It is the cheapest sanity
check on the weights: if a bot doing nothing clever outscores a human playing
well, the formula is wrong, and you will see it immediately.

## Verification

1. Console clean.
2. **Counters are right.** Drive a scripted round: collect 3 known vesicles,
   break 2 cluster members, shatter 1 aggregate block, complete 1 mitosis.
   Every counter matches exactly. Paste the object in `## Findings`.
3. **Distance is frame-rate independent** — the same route at Very Slow and Very
   Fast gives the same distance within a few percent. Multiply by `deltaSec`, not
   by frames; this is the trap the whole codebase's probability rolls already hit.
4. Three worked score examples, as above.
5. Card renders correctly at 390×844, 844×390 and 1280×800; screenshot each.
6. Restart still works with the card up, on keyboard and touch.
7. **No allocation in the hot path** — the stats object is created once per round,
   never per frame (§5).
8. `worldChildren` flat across 20 consecutive rounds; the card does not leak
   between rounds.
9. Regression sweep §7.6.

## Definition of done

- [x] Per-player stats, incremented at the existing event sites
- [x] `scoreRun()` with named constants and three worked examples
- [x] End-of-round card, responsive, non-blocking
- [x] Bots scored too
- [x] Distance frame-rate independent, proven at two speeds
- [x] `docs/TASKS.md`: T53 → `DONE`, T54 → `READY`

---

## Findings

### Where each counter lives

- `p.stats` is built next to `p.effects` in `startRound()`'s `players.push()`
  (same block, can't drift apart): `{ vesicles: {membrane,lysosome,mitochondria},
  clusterBreaks, massBreaks, mitosisEvents, distance, maxGeneration: 1 }`.
- **Vesicles** — one line at the existing type-dispatch site in the vesicle
  pickup loop (`p.stats.vesicles[v.type]++`, right after `boostTarget(p)` is
  computed), keyed by the real `v.type` string (`membrane`/`lysosome`/
  `mitochondria`) rather than the illustrative `speed`/`ghost`/`golgi` names in
  this file's own Design section — those names describe *effects* a single
  membrane-vesicle pickup can non-deterministically trigger (ghost vs. golgi,
  gated by a rolling counter), so keying on the vesicle type actually picked up
  is the one-line, never-re-derived option the task asks for. Credited to the
  picker `p`, not T36's `boostTarget()` redirect target, since "vesicles
  collected" describes what the picker walked over.
- **Cluster/mass breaks** — one line each at the two existing attack-mode break
  sites in `updatePlayers()`: section 0.9 (`breakClusterMember()`/
  `destroyNecroticOrganelle()`, both branches) increments `clusterBreaks`;
  section 1.6 (`malignantMass.blocks.splice()`) increments `massBreaks`.
- **Mitosis events / maxGeneration** — `updateMitosis()`'s existing "8. Cell
  division complete" block (`if (!mitosis.generationCounted) { ... }`), which
  by construction only reaches players still `alive` after section 4 killed
  anyone who didn't make it to Cell B. Both counters bumped together per
  surviving player.
- **Distance** — one unconditional line in `updatePlayers()`'s movement step,
  `p.stats.distance += Math.hypot(nextX - p.x, nextY - p.y)`, placed just
  before `p.x = nextX; p.y = nextY` so it counts gap/ghost movement too (unlike
  `p.traceDist`, which only tracks drawn-trace length). No `deltaSec` multiply
  needed: `nextX/nextY` are already computed from `actualSpeed * delta`, and
  `delta` is PIXI's frame-scaled deltaTime (`dt_seconds * 60`, see
  `window.stepHeadless`'s own comment) — so summing per-frame position deltas
  is frame-rate independent by construction, the same way the trace-drawing
  code already computes `p.traceDist`.

### Score weights and reasoning

```js
const SCORE = { perSecond: 2, perGeneration: 750, perVesicle: 15, perBreak: 50, per100px: 1 };
scoreRun(stats, survivalSeconds) =
    survivalSeconds * perSecond
  + (stats.maxGeneration - 1) * perGeneration
  + vesicleCount * perVesicle
  + breakCount * perBreak
  + (stats.distance / 100) * per100px
```

Generations dominate on purpose: reaching a new generation means surviving a
full mitosis event (`MITOSIS_INTERVAL = 240s`, plus the 120s event itself), the
single largest hazard-density jump in the game, so `perGeneration=750` per
generation is worth roughly 6+ minutes of the `perSecond` term. `per100px=1` is
deliberately small — a mild anti-turtling nudge (a full-round's worth of
distance, tens of thousands of px, still lands in the low hundreds of points),
not a term that could out-weigh a generation jump. Kills are not counted, per
`PHASE8-META-PROGRESSION.md`.

### Three worked examples (computed by the real in-browser `scoreRun()`, not by hand)

| Run | time | maxGen | vesicles (m/l/mi) | breaks (c/m) | mitosis | distance | **score** |
|---|---|---|---|---|---|---|---|
| Timid Gen 1 (hugs the wall, no pickups) | 200s | 1 | 0/0/0 | 0/0 | 0 | 18000px | **580** |
| Aggressive Gen 2 | 260s | 2 | 3/2/3 | 2/1 | 1 | 54600px | **2086** |
| Long Gen 3 | 520s | 3 | 6/5/4 | 3/2 | 2 | 78000px | **3795** |

Timid Gen 1 (580) loses badly to both the aggressive Gen 2 run (2086, 3.6x) and
the long Gen 3 run (3795, 6.5x) — the weights hold.

### Scripted-round counter dump

Vesicle pickup (one of each type, walked over in a single step):
```json
{"before": {"vesicles":{"membrane":0,"lysosome":0,"mitochondria":0},"clusterBreaks":0,"massBreaks":0,"mitosisEvents":0,"distance":216,"maxGeneration":1},
 "afterVesicles": {"membrane":1,"lysosome":1,"mitochondria":1}, "vesiclesLeft":0}
```

Cluster breaks (2 lone necrotic organelles broken in attack mode, cooldown
cleared between them) and one aggregate block shatter:
```json
{"after1": {"clusterBreaks":1,"organellesLeft":25}, "after2": {"clusterBreaks":2,"organellesLeft":25}}
{"massBreaks":1,"blocksLeft":0}
```
(`organellesLeft` returns to 25 -- push 1, break 1, each time -- confirming
`destroyNecroticOrganelle()`'s teardown still runs; `worldChildren` stayed 16.)

Mitosis completion (forced trigger, both players teleported into Cell B before
the forced snap so both survive):
```json
{"state":"idle","gen":2,
 "p0":{"alive":true,"mitosisEvents":1,"maxGeneration":2},
 "p1":{"alive":true,"mitosisEvents":1,"maxGeneration":2}}
```

Every counter matches exactly what was scripted. **Trap hit while writing these
checks, not in the game code:** the harness's `immortal=True` sets `godMode`,
and both break sites are gated `!godMode` (same as the hazards they guard) —
the first cluster/mass-break run silently did nothing under `immortal=True`
until re-run without it.

### Distance: frame-rate independence

`window.stepHeadless(20, dt)` at three step sizes, Speed: Normal (1.5),
`vesicles=[]` cleared first so a stray pickup mid-run can't confound the
comparison (an earlier pass without that clear picked up a speed vesicle only
in the `dt=1/120` run and showed a false 27% divergence — not a distance bug,
a test-isolation bug):

| dt | distance |
|---|---|
| 1/20 (choppy) | 1800px |
| 1/60 | 1800px |
| 1/120 (smooth) | 1800.75px |

Theoretical (`actualSpeed * 60 * 20s` = `1.5 * 60 * 20`) = 1800px. Max deviation
0.04%, well inside "a few percent." Sanity check at two speed settings over the
same 20 game-seconds: Normal (1.5) → 1800px, Very Fast (3.5) → 4200px — exactly
proportional (`3.5/1.5 * 1800 = 4200`).

### Card rendering

Screenshotted (4 players, 2 alive/2 eliminated, varied stats) at 390x844,
844x390 and 1280x800 — readable, no horizontal overflow at any width, no
console errors. On 390x844 and 844x390 the card sits below the pre-existing
menu + control-splash content (which already made `#ui` scroll before this
task, T20/T24) inside the same `overflow-y:auto`/`90dvh` clamp — reachable by
scrolling, not clipped. Restart verified both ways with the card up: `Enter`
(→ `quickPlay()`, the existing `!isPlaying` shortcut) and a real click on
"Start Game" both start a fresh round and hide the card
(`statsCardElement.classList.add('hidden-stats')` in `startRound()`); the new
round's player stats reset to zero.

### Other verification

- Console clean throughout every check above, including a real (non-immortal,
  non-scripted) round where the player drove straight into the membrane with
  no input and the card appeared through the actual game-over path, unforced.
- `worldChildren` flat at 16 across 20 consecutive scripted restarts — the card
  does not leak DOM or PIXI state between rounds (it's plain HTML, not PIXI).
- Regression sweep (§7.6) via direct `checkCollision()` calls at all three
  speeds (1.5/2.5/3.5), 3 bots, ~8.5s real play each: membrane / own-trace /
  organelle all `true` (lethal), the near-miss point on the player's own neck
  `false` (survives) — identical at every speed, console clean.
- `file://` (offline, `dist/`) load: `renderStatsCard()`/`scoreRun()` both work
  identically offline, console clean.
- No allocation in the hot path: `p.stats` is created once per round in
  `startRound()`; `renderStatsCard()` only runs at round end, never per frame.
- `sw.js` `CACHE_NAME` bumped v30→v31; `dist/Cellular_Zatacka.html` rebuilt,
  `--check` passes.
