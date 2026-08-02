# T03 — Hazard/reward channels + steering weight normalization

**Track:** A (Phase 1 gate) · **Depends on:** T02 · **Risk:** low-medium · **Est. diff:** ~110 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Make the bot a usable testing agent: separate what a ray *fears* from what it
*wants*, put both on the same normalized 0..1 scale, and replace the current
threshold steering with a proportional response.

## Why

Two independent defects make the bot survive but behave uselessly.

**1. Unnormalized weights.** In `getRayWeight()`:

```
hazard:  weight -= danger * danger * 5     // danger = maxSense - dist, max 350
                                            // → up to −612,500
vesicle: weight += 2000 * (1 - dist/maxSense)   // → up to +2,000
mitosis: force += diff * 150                    // → up to ±471
```

Hazards outweigh rewards by ~1300×. The bot therefore ignores vesicles almost
entirely, and the mitosis bridge pull is invisible unless every ray is perfectly
clear. It also saturates the ±10 steering threshold constantly, which is the
wobble.

**2. Rewards occlude hazards.** `raycast()` returns on the *first* thing it hits,
including a vesicle. A vesicle floating in front of a wall makes the ray report
`'vesicle'` and the bot cannot see the wall behind it. A reward is not an
obstacle and must not stop the ray.

---

## Prerequisites

Read `raycast()` (post-T01/T02), `getRayWeight()` and `updateBotAI()` in full.

---

## Part 1 — Two channels from one ray

Change `raycast()` to return both channels in one pass:

```
{
  hazard: { dist: <number>, type: <string> },   // nearest lethal thing, or
                                                // {dist: maxDist, type:'clear'}
  reward: { dist: <number>, raw: <object> } | null   // nearest vesicle, or null
}
```

Rules:

- A vesicle hit **records** `reward` (nearest wins) and **continues** marching.
- Any lethal hit sets `hazard` and **stops** the ray, as today.
- A vesicle *behind* the hazard must not be recorded — since the march is
  ordered, simply stop recording once the hazard is found.
- Reuse one module-level scratch object for the return value if you can do so
  safely; if not, a fresh literal per ray (3/bot/frame) is acceptable. Do **not**
  allocate inside the march loop.

`raycast()` currently has exactly one other caller pattern to check: search the
file for `raycast(` and update every call site. As of T02 the only callers are in
`updateBotAI()`.

## Part 2 — Normalized scoring

Delete `getRayWeight()` and replace it with two small pure functions on a 0..1
scale. Suggested shape — tune the exponent, not the range:

```
// 0 = wall in your face, 1 = nothing within maxSense
function hazardScore(hazard, maxSense) {
    if (hazard.type === 'clear') return 1;
    let n = Math.min(1, hazard.dist / maxSense);
    return n * n;          // quadratic: cheap far away, urgent up close
}

// 0 = no reward, 1 = reward touching the head
function rewardScore(reward, maxSense) {
    if (!reward) return 0;
    return 1 - Math.min(1, reward.dist / maxSense);
}
```

Then combine into a single signed steering force in `updateBotAI()`, where every
term is explicitly weighted and every weight is a **named constant declared
together at the top of the function** so they can be tuned in one place:

```
const W_AVOID   = 1.0;   // lateral hazard asymmetry
const W_FORWARD = 1.6;   // forward hazard escape
const W_REWARD  = 0.35;  // vesicle attraction
const W_BRIDGE  = 0.5;   // mitosis pull
const PANIC     = 0.25;  // below this forward hazard score, rewards are ignored
```

Force assembly (all terms now land in roughly the same −2..+2 range):

1. **Lateral avoidance** — `force += (hazardScore(right) - hazardScore(left)) * W_AVOID`.
   Positive force turns right, matching the existing convention; verify the sign
   against the existing code before trusting this line.
2. **Forward escape** — if `hazardScore(forward) < 1`, push toward the side with
   the higher hazard score (the clearer side), scaled by
   `(1 - hazardScore(forward)) * W_FORWARD`.
3. **Reward pull** — only if `hazardScore(forward) > PANIC` and both laterals are
   above `PANIC`: `force += (rewardScore(right) - rewardScore(left)) * W_REWARD`.
4. **Bridge pull** — keep the existing `atan2` angle-difference logic, but
   normalize: `diff / Math.PI` is in −1..1, then `* W_BRIDGE`. Apply only when
   `mitosis.state !== 'idle'`, as today.

## Part 3 — Proportional steering

Replace the `if (force < -10) ... else if (force > 10)` threshold with a
proportional turn, clamped to the same maximum rate a human has:

```
const MAX_TURN = 0.08;                        // must equal the human turn rate
let turn = Math.max(-1, Math.min(1, force));  // clamp the normalized force
if (Math.abs(turn) > 0.05) {                  // small dead-zone kills wobble
    bot.angle += turn * MAX_TURN * delta;
}
```

`MAX_TURN` must stay identical to the human rate in `gameLoop`
(`p.angle -= 0.08 * delta`). If a future task changes the human rate, this must
change with it — note that in a comment.

## Part 4 — targetMode logic

Keep the existing intent, adapted to the new shape:

- `bot.targetMode = 'self'` when a reward is present and closer than the forward
  hazard.
- `bot.targetMode = 'attack'` when the forward hazard is a `'trace'` within 150px
  **and** `bot.effects.speedTimer > 0`.

Do not add new behaviours (no hunting, no vesicle-type preference) — that is
outside this task.

---

## Files touched

`260703_Cellsnake.html` only: `raycast()` return shape, `getRayWeight()` deleted
and replaced, `updateBotAI()` rewritten.

---

## Verification

Behavioural, so be systematic. Run each for a full 60 seconds.

1. Console clean.
2. **Survival did not regress.** 1 player + 1 bot, Normal speed, 5 rounds. Record
   the bot's survival time each round. Median must be **≥** the pre-change median.
   Measure the pre-change baseline first, before you edit anything.
3. **Rewards are now used.** The bot must visibly divert toward vesicles when no
   hazard is near. Watch 60s in an open area; it should collect at least one.
   Before this change it essentially never did.
4. **Bridge is used.** Fast-forward to mitosis. The bot must head toward Cell B
   rather than wandering.
5. **Wobble is gone.** Watch a bot on a straight open run — the trace should be
   smooth, not a visible zigzag.
6. **Occlusion fixed.** Confirm by temporary logging that a ray reporting a
   reward can also report a hazard in the same call. Remove the logging before
   committing.
7. Regression sweep from `AGENT_CONDUCT.md` §7.6.

## Definition of done

- [ ] `raycast` returns `{hazard, reward}`; vesicles no longer stop the ray
- [ ] All steering terms normalized to a comparable range
- [ ] All tuning weights are named constants in one block
- [ ] Steering is proportional with a dead-zone; `MAX_TURN` equals the human rate
- [ ] Baseline vs. after survival times recorded in the commit message
- [ ] `docs/TASKS.md`: T03 → `DONE`, T19 → `READY` if its other deps are met
