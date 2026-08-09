# T52 — Generation 4 reads as "vesicles drift oddly"

**Track:** K · **Depends on:** T15 · **Risk:** low-medium · **Est. diff:** ~60 lines

Owner report, 2026-08-09: *"For Gen4 I am not sure what is happening; I only
noticed vesicles moving towards the nucleus. What is supposed to happen there?"*

The owner's description is **complete and correct** — that genuinely is all Gen 4
does. Which is the problem.

---

## What T15 actually shipped

Gen 4 is *angiogenesis*: a gravity well at each cell centre.

```js
const GRAVITY_ACCEL_PER_TICK = 12 / 60;  // 12 px/s^2 inward
const GRAVITY_MAX_V_PER_TICK = 60 / 60;  // 60 px/s terminal
const GRAVITY_CONSUME_RADIUS = 150;      // despawn before the 130px lethal core
```

Vesicles — and only vesicles — accelerate toward the centre and **despawn** at
150px. Plus faint pulsing rings at the cell centre. Nothing else changes.

The intended pressure is real: pickups drain toward the nucleus and are
destroyed, so collecting anything means chasing it inward toward the one part of
the arena that kills on contact, and waiting costs you the pickup entirely.

Three things stop the player feeling that:

1. **The stake is invisible.** A vesicle that despawns 150px out looks like it
   faded, not like the cell ate it. There is no consume event, no count, no sound
   or burst — nothing that says *you just lost that*.
2. **The rings are too faint to name the mechanic.** At the camera zooms measured
   in T47 (0.17–0.44 in shared camera) a faint pulsing ring at the centre is
   invisible. The player never sees a "well", only its symptom.
3. **Nothing else in the arena reacts.** The player, the trace, the organelles
   and the aggregate all ignore the well, so it reads as a vesicle quirk rather
   than as a property of the cell.

Note the help panel (T41) *does* describe Gen 4. The owner read the panel and
still could not tell — so this is not a documentation fix.

## The work

Make the existing mechanic legible before adding anything to it. In order:

1. **Show the consume.** A T17 burst from the **existing pooled emitter** when a
   vesicle is consumed, drawn inward, plus a brief flare on the well. The player
   must see the cell take it.
2. **Make the well visible at low zoom.** Scale the ring's size/alpha against
   `world.scale.x` so it holds up at 0.2, or replace it with an inward-drifting
   particle stream that reads as flow at any zoom. Screenshot at 0.2, 0.4 and 1.0.
3. **Telegraph the pull on entry to Gen 4.** The generation banner already fires;
   give the well a one-off establishing pulse so the player connects cause to
   effect the first time.

Then **one** gameplay hook, chosen and justified — do not do several:

- **(a) The pull acts on the player too**, weakly, and only near the centre.
  Turns Gen 4 into a genuine spatial hazard around an already-lethal nucleus.
  Strongest option; also the riskiest, because it touches the movement path that
  every collision test is built on. If chosen, the fixed-timestep concerns in
  T28 apply — say how you kept the pull frame-rate independent.
- **(b) Consumed vesicles feed the well**, which grows: radius or strength rises
  with each one eaten, so neglect compounds. Mirrors T38's necrosis loop, which
  the owner liked.
- **(c) The player can intercept.** Collecting a vesicle already inside the pull
  radius is worth more — a longer effect, or a small score bonus once T53 exists.
  Rewards the risk instead of only punishing the delay.

Recommendation: **(b)**, then **(c)** as a follow-up task. (a) is the most
interesting but is the one that can break collision, and T22 (sim/render split)
is queued right behind this — do it after that lands, not before.

## Verification

1. Console clean.
2. **Gen 1–3 completely unaffected.**
3. Screenshots of the well at `world.scale.x` ≈ 0.2, 0.4 and 1.0 — recognisable
   as a well at all three. This is the core test; T47 has the zoom numbers.
4. Consume events visible: record how many vesicles are consumed per minute at
   Gen 4 and confirm each produced a burst.
5. Whichever hook is chosen, measure it: growth curve for (b), pull force on the
   player for (a), value delta for (c). Numbers in `## Findings`.
6. **Particles stay pooled** — peak `particleCount` under `MAX_PARTICLES` with
   the well consuming at its maximum rate.
7. Bots are not broken by it — 2 minutes at Gen 4, bots still collect and do not
   suicide into the nucleus chasing drifting vesicles.
8. `worldChildren` flat over 10 minutes at Gen 4.
9. Help panel updated from live constants.
10. Regression sweep §7.6.

## Definition of done

- [ ] Consume is visible; well is legible at 0.2 zoom
- [ ] One gameplay hook chosen, implemented, measured
- [ ] Bots unaffected; particles pooled; no leak
- [ ] Help panel matches
- [ ] `docs/TASKS.md`: T52 → `DONE`

---

## Findings

*(Which hook and why; zoom screenshots; consume rate; the measured effect.)*
