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

- [ ] `freeUntil` window before the pull applies; length reported
- [ ] Feed meter, per-type weights, rises only on consume
- [ ] Progress bar, responsive, with the consume event visible
- [ ] Window shrinks to zero as the meter fills — direct-feed phase reached
- [ ] Well legible at 0.2 zoom
- [ ] Denial proven with two measured runs
- [ ] Bots unaffected; no leak
- [ ] `docs/TASKS.md`: T52 → `DONE`, T57 → `READY`

---

## Findings

*(Window length and how it scales; per-type weights and why; the two denial runs;
time to full meter with and without collection; zoom screenshots.)*
