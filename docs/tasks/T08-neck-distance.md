# T08 — Distance-based self-neck immunity

**Track:** B · **Depends on:** T07 · **Risk:** low-medium · **Est. diff:** ~40 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Replace the fixed 15/16-frame self-collision immunity window with a
distance-based one, so the "immune neck" is the same physical length at every
speed setting.

## Why

Two places grant a player immunity against their own most recent trace:

- `checkCollision()`: `let skipFrames = (item.playerId === player.id) ? 15 : 0;`
  then `if (isLastSegment && item.i >= item.segLength - skipFrames - 1) continue;`
- `raycast()`: `if (isLastSegment && item.i >= item.segLength - 16) continue;`

A frame count is speed-dependent. One trace point is appended per frame at
`currentSpeed` pixels of travel, so the immune neck is:

| Speed setting | `currentSpeed` | Neck length |
|---|---|---|
| Normal | 1.5 | ~22 px |
| Fast | 2.5 | ~37 px |
| Very Fast | 3.5 | ~52 px |

Speed power-ups add another +1.0 or +2.0, pushing it to ~80px. So the turning
circle a player can safely execute silently changes with the speed setting and
with power-up state — a fairness and tuning problem, and a source of
"why did I die there?" reports.

The bot is affected too: `raycast` uses a hard-coded 16 that does not even match
`checkCollision`'s 15, so the sensor and the physics disagree by one frame.

---

## Prerequisites

Read: the trace branch of `checkCollision()`, the trace branch of `raycast()`,
`rebuildSpatialGrid()`'s trace item shape, the trace append site in `gameLoop`,
and T07's `MIN_TAIL_POINTS` constant.

---

## Design

### Store cumulative distance on each trace point

The cheapest correct approach. Where a trace point is appended in `gameLoop`,
also store the running distance along the trace:

```
seg.push({ x: nextX, y: nextY, d: prevD + stepLength });
```

where `prevD` is the previous point's `d` (0 for a new segment) and `stepLength`
is the distance actually moved this frame. Each player also tracks
`p.traceDist` — the total distance travelled — so the head's distance is known
without walking the array.

**Backwards compatibility:** every existing reader of trace points uses `.x` and
`.y` only (`drawTraces()`, `rebuildSpatialGrid()`, `deleteOldestTrace()`,
T07's trimmer). Adding a third field breaks nothing. Verify by searching for
`seg[` and `.traceSegments` and reading each hit.

### Carry the distance into the grid item

In `rebuildSpatialGrid()`'s trace insert, add the segment's own distance:

```
spatialGrid.insertSegment(..., { type:'trace', ..., d: seg[i].d });
```

Do not add anything else — this object is created once per point per frame and is
the hottest allocation in the file.

### The immunity test

Replace both index-based tests with one shared predicate:

```
const NECK_LENGTH = 35;   // px of own trace that cannot kill you

// true if this trace item is inside the caster's own immune neck
function isOwnNeck(item, owner) {
    return item.playerId === owner.id
        && item.s === owner.traceSegments.length - 1
        && (owner.traceDist - item.d) < NECK_LENGTH;
}
```

Use it in **both** `checkCollision()` and `raycast()`. One definition, two call
sites — this is the point of the task. Note that `raycast`'s caster is looked up
by `casterId`; T01 already hoisted that lookup.

### Choosing `NECK_LENGTH`

Pick the value that preserves current feel at the default speed: Normal speed
gives ~22px today, Very Fast gives ~52px. **35px** is a reasonable middle. Play
all three speeds and adjust; record what you chose and why in the commit message.

Sanity bound: `NECK_LENGTH` must be comfortably larger than
`maxSpeed * maxDelta` (≈5.5px × ~2 = 11px) so a single frame's step can never
jump the whole neck, and comfortably smaller than the player's minimum turning
circle circumference so tight turns still kill.

### Interaction with T07

T07's `MIN_TAIL_POINTS = 32` was derived from the 16-frame window. Re-derive it:
the last segment must always retain at least `NECK_LENGTH` worth of distance, so
the floor becomes distance-based too. Update T07's constant and its comment as
part of this task.

---

## Files touched

`260703_Cellsnake.html` only: trace append site in `gameLoop`, `p.traceDist`
initialisation in `startRound()`'s player literal and on segment breaks,
`rebuildSpatialGrid()` trace item, new `isOwnNeck()` + `NECK_LENGTH`,
`checkCollision()`, `raycast()`, T07's `MIN_TAIL_POINTS`.

Watch the gap mechanic: when `p.isGap` ends a segment and a new one starts,
`d` restarts — but `owner.traceDist` must **not** reset, or the immunity
calculation breaks across the gap. Read the gap logic (`GAP_CHANCE`,
`GAP_LENGTH`, `gapCounter`) before writing this.

---

## Verification

1. Console clean.
2. **Same feel at Normal speed.** Play 3 minutes at Normal. Tight-turn deaths
   must feel unchanged from before the task.
3. **Consistency across speeds.** At each of the three speeds, hold a full-rate
   turn from a standstill-equivalent straight run and measure how tight a circle
   you can complete without dying. The three should now be comparable; before,
   Very Fast was ~2.4× more forgiving.
4. **Sensor and physics agree.** Confirm the bot no longer treats its own neck
   differently from what the physics allows — with a temporary log, assert that
   `isOwnNeck` returns the same answer for the same item in both call paths.
      Remove the logging before committing.
5. **Speed power-up.** Collect a speed vesicle and repeat test 3. The neck length
   must not change.
6. **Gaps.** Verify a player can pass through their own gap and that the
   immunity does not leak across a segment break.
7. Regression sweep from `AGENT_CONDUCT.md` §7.6.

## Definition of done

- [ ] Trace points carry cumulative distance `d`
- [ ] One `isOwnNeck()` predicate used by both `checkCollision` and `raycast`
- [ ] The 15 / 16 mismatch is gone
- [ ] `NECK_LENGTH` chosen with a stated rationale
- [ ] T07's `MIN_TAIL_POINTS` re-derived
- [ ] Gap-crossing behaviour verified
- [ ] `docs/TASKS.md`: T08 → `DONE`
