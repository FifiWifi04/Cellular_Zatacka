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

- [ ] Per-player stats, incremented at the existing event sites
- [ ] `scoreRun()` with named constants and three worked examples
- [ ] End-of-round card, responsive, non-blocking
- [ ] Bots scored too
- [ ] Distance frame-rate independent, proven at two speeds
- [ ] `docs/TASKS.md`: T53 → `DONE`, T54 → `READY`

---

## Findings

*(Weights and why; the scripted-round counter dump; the three worked examples;
the distance measurement at both speeds.)*
