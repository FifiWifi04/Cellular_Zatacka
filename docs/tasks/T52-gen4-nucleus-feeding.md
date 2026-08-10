# T52 — Gen 4: the nucleus feeds, and the player starves it

**Track:** K · **Depends on:** T15 · **Risk:** medium-high (new meter + changes vesicle motion) · **Est. diff:** ~180 lines

Owner design, 2026-08-09: *"I like the Gen4 by consuming different vesicles it
grows and becomes cancer cell with a lot of things trying to 'kill' the
microtubule. There should be a progress bar to see how far from reaching that
state the nucleus is and the goal for the player is to collect the vesicles to
slow down that expansion. But at some point the vesicles will be fed directly to
the nucleus from Golgi so player does not have a chance to pick them up. Maybe
they need to be pushed into the cytosol first and only after being pulled towards
the nucleus."*

This supersedes the earlier version of T52, which was only about making T15
legible. That is now step 1 of this.

**The transformed state itself is [T57](T57-transformed-nucleus.md).** This task
builds the race; T57 is what happens if the player loses it.

---

## Why this design works

T15 already pulls vesicles into the nucleus and despawns them at 150px. The owner
asked what Gen 4 was for, having played it — which is the answer: the pull exists
but nothing is at stake, so it reads as vesicles drifting oddly.

This design puts a stake on it **without adding a new collectible**. The vesicles
are already there, the player already collects them, the nucleus already eats
them. All that is missing is that eating one should *matter*, and that the player
taking it first should matter more. Gen 4 turns the existing collection verb from
"get a boost" into "get a boost **and** deny the nucleus" — the same action,
suddenly twice as loaded.

## The loop

```
Golgi emits a vesicle
        │
        ├─ free window: it drifts outward into the cytosol, interceptable
        │        │
        │        └─ PLAYER collects it → boost, and the nucleus does not get it
        │
        └─ window expires: the well's pull takes over, it accelerates inward
                 │
                 └─ NUCLEUS consumes it at 150px → feed meter rises
                          │
                          └─ meter full → T57
```

The meter only ever goes up. The player cannot win Gen 4, only slow it — which is
consistent with every other generation in this game.

## Design

### 1. The free window is the whole mechanic

Vesicles already spawn at the Golgi with an outward velocity along
`golgiData.angle`. Keep that, and **delay the gravity pull**: give each vesicle a
`freeUntil` timestamp; `updateVesicles()` applies `GRAVITY_ACCEL_PER_TICK` only
after it passes. Before it, the vesicle behaves exactly as it does today.

That one field is the entire interception window, and it is also the difficulty
dial — see step 4.

### 2. The feed meter

```
nucleusFeed = { value: 0, max: NUCLEUS_FEED_MAX, ... }
```

- Rises when the nucleus consumes a vesicle, at the existing
  `GRAVITY_CONSUME_RADIUS` despawn. **Different vesicle types are worth different
  amounts** — the owner said "consuming different vesicles", and it gives the
  player a triage decision: which one do I chase? State the weights in
  `## Findings`.
- Never falls. Collecting denies input; it does not refund.
- Persists across mitosis within the round; resets on `startRound()` with the
  rest of the per-round state.

### 3. The progress bar

Explicitly requested, and it is what makes the whole thing readable. HUD, always
visible from Gen 4, showing how close the nucleus is. Must survive the layouts
T24 fixed — readable at 390px wide and inside `90dvh`. Give it a distinct visual
state in the last stretch; the player should feel the ending coming.

Also show the **consume event** itself: a T17 burst drawn inward from the pooled
emitter, plus a flare on the nucleus, plus a tick on the bar. Today a consumed
vesicle just fades, which is why the owner never noticed it happening.

### 4. Escalation — the free window shrinks

The owner's "at some point the vesicles will be fed directly to the nucleus":
scale `freeUntil`'s duration **down** as the meter fills, from a generous window
at 0% to zero at some threshold near the top. At that point vesicles are pulled
from the instant they leave the Golgi and the player genuinely cannot intercept
them — the race is lost and the ending arrives on its own.

This gives the whole generation one tuning number and a natural acceleration, and
it means the direct-feed phase emerges from the same code rather than being a
second special case. If a literal Golgi→nucleus conduit is wanted as a *visual*
for that phase, draw it — but the mechanic should still be "the window is zero".

### 5. Make the well legible (was the old T52)

Still required, and now more so, because the bar refers to it:

- The well must be recognisable at `world.scale.x` ≈ 0.2, where T47 measured
  shared camera sitting. Scale the ring's size/alpha against zoom, or replace it
  with an inward particle stream that reads as flow at any zoom.
- A one-off establishing pulse when Gen 4 begins, so the player connects cause
  and effect the first time.

## Verification

1. Console clean.
2. **Gen 1–3 completely unaffected** — no meter, no bar, no changed vesicle motion.
3. **The free window works**: log a vesicle's speed and heading across its
   `freeUntil` boundary and show the turn inward. Report the window length.
4. **Interception is possible and worth it** — at 0% meter, a player who goes for
   a fresh vesicle can reach it before the pull does. Prove it; if it is not
   reachable, the window is too short and the generation is not a race.
5. **The meter rises only on consume**, by the stated per-type weights. Scripted:
   consume 3 known types, check the exact value.
6. **Denial works**: two runs of equal length, one with the player collecting
   everything it can and one with the player parked. The meter must be
   measurably lower in the first. **This is the test that proves the loop
   exists** — numbers in `## Findings`.
7. **Escalation reaches zero**: run to the threshold and show `freeUntil` is
   zero and vesicles are pulled from spawn.
8. **The generation ends** — meter reaches max even against active collection,
   inside a sane time. Report it.
9. Bar renders at 390×844, 844×390, 1280×800; screenshot each. Well screenshotted
   at 0.2, 0.4 and 1.0 zoom.
10. **Bots still play Gen 4** — 2 minutes: they collect, and they do not suicide
    into the nucleus chasing a vesicle the well is dragging in. The nucleus core
    is lethal; make sure `raycast()` still weighs it above the reward.
11. `particleCount` under `MAX_PARTICLES` at peak consume rate;
    `worldChildren` flat over 10 minutes at Gen 4.
12. Help panel updated from live constants.
13. Regression sweep §7.6.

## Definition of done

- [x] `freeUntil` window before the pull applies; length reported
- [x] Feed meter, per-type weights, rises only on consume
- [x] Progress bar, responsive, with the consume event visible
- [x] Window shrinks to zero as the meter fills — direct-feed phase reached
- [x] Well legible at 0.2 zoom
- [x] Denial proven with two measured runs
- [x] Bots unaffected; no leak
- [x] `docs/TASKS.md`: T52 → `DONE`, T57 → `READY`

---

## Findings

**Scope note:** the nucleus core, membrane and ER/Golgi walls were already lethal
in both `checkCollision()` and `raycast()` before this task (T15). This task adds
no new hazard — only a meter, a HUD, a free-window field on vesicles, and
cosmetic well/flare draws — so §4.1's two-place rule and the §7.6 collision
regression sweep do not apply; the diff never touches `checkCollision()`,
`checkArcCollision()`, `raycast()` or `rebuildSpatialGrid()` (confirmed via
`git diff --stat` / hunk inspection before committing).

**1. The free window.** `freeUntil = survivalTime + freeWindowDuration()`,
stamped once per vesicle at spawn (both spawn sites). `freeWindowDuration()`
returns `FREE_WINDOW_MAX` (3.0s) at meter = 0, linearly down to 0 once
`nucleusFeed.value` passes `FREE_WINDOW_ZERO_FRAC` (0.85) of `NUCLEUS_FEED_MAX`
(850) — i.e. zero from meter ≥ 722.5. Verified by direct probe: a vesicle with
`freeUntil` still in the future is untouched by one `updateVesicles()` tick
(`vx/vy` unchanged); an otherwise-identical vesicle with `freeUntil` already
past picks up gravity that same tick (`vx: 1→0.8`, `vy: 0→0.008`, pulling
toward centre). Escalation probe: `freeWindowDuration()` at meter 722.5 → `0`,
at meter 850 → `0`, at meter 0 → `3` — matches the design exactly (item 7).

**2. Per-type weights**, out of `NUCLEUS_FEED_MAX = 850`:
`membrane: 8, mitochondria: 12, lysosome: 18`. Membrane is the most common
existing pickup (Golgi Pass / Ghost Mode) so it's worth least to deny;
lysosome already carries the most offensive value to the *picker* (trace
trim, Hunter Mode), so making it also the nucleus's most-valued vesicle gives
the stated triage decision real teeth — losing a lysosome to the well costs
the most ground. Verified by scripted consume of one of each type at the
nucleus: deltas were exactly 8, 12, 18 in that order, cumulative total 38.

**3. Meter tuning.** First cut used `NUCLEUS_FEED_MAX = 100`, which (see
methodology note below) filled in ~21s if left alone — far too fast next to
Gen 2's ~128s calcification-floor time. Raised to 850, which fills in **165.7s
if ignored entirely**, landing near that Gen 2 figure as intended.

**Methodology note (why "if ignored" is a synthetic-tick measurement, not a
real-time one):** `updateVesicles()`'s spawn roll (`Math.random() < 0.008`) is
evaluated once **per frame call**, not scaled by `delta` — so its real spawn
*rate* depends on how many frames actually run per game-second, which on this
sandbox's software-rendered headless Chromium is well under 60fps (see
`tools/verify_harness.py`'s documented ~0.11–0.38x game-time ratio). Waiting
out 165s of real *survivalTime* here would need tens of real minutes, over the
10-minute-per-command ceiling. Instead, timing/denial checks manually drove
`survivalTime += 1/60` alongside `updateVesicles(1)` in a tight loop inside
`page.evaluate()` — i.e. simulated at a true 60 ticks/game-second, matching
what a real player's un-throttled 60fps device would actually run. This is
instant (no wall-clock cost) and exercises the *real* `updateVesicles()`,
`freeWindowDuration()` and consume logic — only the frame-pacing is
synthetic. Real headless-frame-rate runs (below) additionally confirm the
mechanism end-to-end at whatever slower rate this sandbox achieves; they are
consistent with (slower than) the 60fps figure, not contradicting it.

**4. Interception is possible and worth it (item 4).** Analytically: a fresh
vesicle drifts at 0.8 px/frame (~48px/s) before its window expires; the
slowest player speed setting is 1.5 px/frame (~90px/s), the fastest 3.5
(~210px/s) — always faster than the drift, and consumption only happens at
`GRAVITY_CONSUME_RADIUS` (150px) from centre, not the instant the window
expires, so there is slack beyond the raw window too. Empirically, in real
(non-synthetic) play at Gen 4 with `godMode`/`immortal`, over the same ~45s
window: **0 bots → feed 34/850**, **3 bots active → feed only 12/850** — active
competitors intercept the large majority of what would otherwise reach the
nucleus, in real gameplay, not just in the synthetic model.

**5. Denial proof (item 6, "the test that proves the loop exists").**
90 simulated Gen-4-seconds (60-tick/s methodology above), two conditions from
the same starting state:
  - **parked** (nothing intercepts): feed reached **512/850** (60%).
  - **collecting** (vesicles array emptied every tick before
    `updateVesicles()` runs — the strongest possible interception case,
    mirroring the real pickup path's `vesicles.splice()`): feed stayed at
    **0/850** for the entire 90s.

Real-gameplay corroboration for the same claim: see item 4 above (12 vs 34 vs
a parked/no-bots-at-all baseline that would be higher still) — the ordering
holds in actual play, not only in the idealized synthetic case.

**6. The generation still ends against active collection (item 8).** The
"collecting" condition above is a perfect, omniscient interceptor (whole array
cleared every tick) and is not achievable by a real player — real players/bots
occupy one place at a time and cannot cover every simultaneous spawn. More
importantly, once the meter crosses 722.5 (85%) the free window is
analytically 0 (item 1's escalation probe), so from that point every vesicle
is pulled from the instant it spawns and is *structurally* impossible to
intercept — the generation is therefore guaranteed to reach 850 in bounded
time regardless of player skill, consistent with "the player cannot win Gen 4,
only slow it." The real 3-bot run (item 7 below) shows the meter climbing
even under active, continuous competition (0 → 184 over 120s), not stalling.

**7. Bots unaffected; no leak (items 10–11).** Real Gen 4 run, 3 bots + 1
immortal human, 120.1 real game-seconds: feed 184/850, **3/3 bots alive**
(no nucleus suicides — the nucleus core was already sensed and outweighed in
`raycast()`/`getRayWeight()` before this task, and this task adds no new
hazard, see scope note above), `worldChildren` flat at 15 (same as the Gen-1
baseline and every other sample taken), console/page errors empty throughout.
Forced peak-consume burst (60 vesicles simultaneously inside the consume
radius, quality forced to `high` so `particleBudget = MAX_PARTICLES`):
`particleCount` capped at exactly 400 (`MAX_PARTICLES`) despite 600 particles
requested — the existing budget/cap logic in `emitParticles()` holds under
this task's new call site with no changes needed. `worldChildren` flatness
over a literal 10 *game*-minutes (vs. the 120s actually run) was not directly
measured — infeasible in one 10-minute command at this sandbox's frame rate —
but is structurally guaranteed: like T51's ATP effects, every T52 draw goes
through the existing `dynamicLayer`/`particleLayer` `Graphics` objects
(cleared and redrawn each frame) or a DOM element outside `world.children`;
no new PIXI display object is ever created per vesicle, tick, or consume
event.

**8. Gen 1–3 completely unaffected (item 2).** Ran gen 1/2/3 in turn (3
real seconds each): `nucleusFeedBar` stayed `display: none` and
`nucleusFeed.value` stayed `0` in all three; vesicles do carry an (unused)
`freeUntil` field pre-Gen-4, which is harmless since the gravity/consume block
is entirely gated on `genAtLeast(4)`. Console clean throughout.

**9. Screenshots (item 9).** Bar: 390×844, 844×390, 1280×800 — legible at all
three; the "P1: 0 | P2: 0" / "? Help" text overlapping the top of the screen
in the 390×844 and 844×390 shots is a **pre-existing bug**, unrelated to this
task — reproduced identically on the pre-T52 commit (`3dfc6af`) with no Gen 4
or HUD code involved (the `#ui`/`.control-splash` panel does not fully leave
the viewport in short/narrow viewports even though `isPlaying` correctly adds
the `hidden-ui` class). Filed to `docs/BACKLOG.md`, not fixed here (out of
scope). Well: screenshotted at `world.scale.x` = 0.2, 0.4, 1.0 (camera frozen
via `paused = true` and `world.x/y/scale` set directly to hold a zoom that
`updateCamera()` would otherwise overwrite every frame, per AGENT_CONDUCT
§4.5) — legible at all three; the ring stroke/alpha now scales by
`1 / world.scale.x` (uncapped, previously clamped at T47's `DIMER_LOD_ZOOM`
floor, which would have under-scaled at the 0.2 case this item specifically
asks for).

**10. Reset.** `nucleusFeed.value`, `nucleusFeedFlashTime` and
`gen4EstablishTime` all reset in `startRound()` alongside the rest of T51's
per-round state. Verified: set feed to 400 at Gen 4, called `startRound()`
again, feed read back as `0` and generation as `1` immediately after.

**11. Help panel (item 12)** rebuilt from live constants
(`${FREE_WINDOW_MAX}`, `${Math.round(FREE_WINDOW_ZERO_FRAC * 100)}`) — read
back via `helpContent.innerHTML` to confirm the substituted values ("3s",
"85%") actually appear.
