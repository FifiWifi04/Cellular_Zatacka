# T07 — Bound trace growth (per-player point cap)

**Track:** B · **Depends on:** T06a · **Risk:** medium (changes gameplay) · **Est. diff:** ~50 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Give each player a hard cap on total stored trace points, trimmed from the front,
so memory and grid-rebuild cost are bounded independently of round length and
vesicle pickups.

## Why

Traces grow at roughly **3,600 points per player per minute** and are never
trimmed except by the `deleteOldestTrace()` power-up path. `rebuildSpatialGrid()`
walks every segment of every player every frame and calls `insertSegment()` per
point-pair, so per-frame cost is linear in total trace length. In a long round
with 4 players that is a steadily rising floor under the whole frame budget.

T06a's run B measures exactly this. Use its numbers to pick the cap.

**Read `docs/reports/soak-B/soak.csv` before choosing constants.** If run B shows no meaningful
degradation at 30 minutes, consider setting the cap generously high (memory
bound only) and note that in the commit message.

---

## Prerequisites

Read: `rebuildSpatialGrid()`, `drawTraces()`, `deleteOldestTrace()`, the trace
append site in `gameLoop` (search for `traceSegments`), and `checkCollision()`'s
trace branch — specifically the self-immunity logic that depends on
`item.s === other.traceSegments.length - 1` and `item.i >= item.segLength - 16`.

---

## Design

### The cap

```
const MAX_TRACE_POINTS = 3600;   // ≈60s of trace at Normal speed; tune from T06a
```

Applied **per player**, counted across all of that player's `traceSegments`.

### Trimming

Once per frame, after appending the new head point, if a player's total exceeds
the cap, remove points from the **front** (oldest first) until it is at or under
the cap:

- Remove whole segments from the front of `traceSegments` while
  `traceSegments[0].length <= excess`.
- Otherwise `splice(0, excess)` the front segment.
- **Never let `traceSegments` become empty** — `deleteOldestTrace()` already
  handles this by pushing `[]`; copy that guard exactly.
- Segments of length < 2 are skipped by `drawTraces()` and produce no grid
  entries, so a trimmed-to-1-point segment is harmless but wasteful — drop
  segments that fall below 2 points, unless it is the last segment (the one
  currently being appended to).

`deleteOldestTrace()` already implements front-trimming by percentage. **Reuse it
rather than writing a second trimmer**: add a sibling
`trimTraceToCap(player, maxPoints)` next to it and keep the two implementations
sharing the same segment-removal loop, or refactor `deleteOldestTrace` to call
the new one. Prefer the smallest diff.

### Where to call it

In `gameLoop`, in the per-player update, immediately after the new trace point is
appended and before anything reads the trace. Do **not** call it inside
`rebuildSpatialGrid()` — that function must stay a pure read of game state.

---

## The self-immunity interaction — read this carefully

Both `checkCollision()` and `raycast()` skip the caster's own trace near the head:

```
isLastSegment && item.i >= item.segLength - 16
```

This is indexed from the **end** of the last segment, so front-trimming does not
affect it. Good — but confirm it, because getting this wrong makes players
randomly die to their own neck.

The dangerous case is trimming the *last* segment (the one the head is appending
to) down near or below 16 points. That can only happen if the cap is very small
or a single segment holds almost the whole budget. Guard it:

**Never trim the last segment below 32 points.** If the cap can only be met by
cutting into the last segment below that floor, stop trimming and accept a
temporary overshoot. Add this as an explicit constant with a comment explaining
why (`MIN_TAIL_POINTS = 32; // must stay > the 16-frame self-immunity window`).

T08 replaces the frame-count immunity with a distance-based one — when it lands,
this floor must be re-derived from the distance, not the count. Note that in the
comment.

---

## Gameplay impact — call it out

This **is** a gameplay change: old trace disappears. At `MAX_TRACE_POINTS = 3600`
and Normal speed that is about a minute of history, which is longer than most
rounds — but in a long solo survival run the map will visibly clear behind the
player.

Two things to do about it:

1. Make the trimming **visually plausible**, not a hard pop. The cheapest
   acceptable option is to just let it disappear (Zatacka-like games do this).
   Do not build a fade in this task; log "trace fade-out on trim" in
   `docs/BACKLOG.md` as a Phase 4 juice candidate.
2. Verify it does not break the mitosis and infection events, which assume traces
   persist.

If the owner has not confirmed they want this gameplay change, implement it
behind a constant set high enough to be a pure memory bound
(e.g. `MAX_TRACE_POINTS = 20000`, ~5.5 minutes) and note in the commit message
that the aggressive value is a one-line change.

---

## Files touched

`260703_Cellsnake.html` only: new constants, new `trimTraceToCap()` beside
`deleteOldestTrace()`, one call site in `gameLoop`.

---

## Verification

1. Console clean.
2. **Cap holds.** With T04's HUD, run 4 bots in god mode for 5 minutes and watch
   `tracePoints`. It must plateau at `4 × MAX_TRACE_POINTS`, not climb.
3. **Grid cost bounded.** Log `spatialGrid.cells.size` and the wall time of
   `rebuildSpatialGrid()` at 1, 3 and 5 minutes. All three must be flat after the
   cap engages. Put the numbers in the commit message.
4. **No self-neck deaths.** Play a human round for 3 minutes at Very Fast,
   deliberately making tight loops after the cap engages. You must not die to
   your own recently-drawn trace.
5. **Trimming does not desync rendering.** `drawTraces()` and
   `rebuildSpatialGrid()` must always agree — no visible trace that is not
   lethal, no lethal trace that is not visible. Test by driving into the oldest
   visible part of your own trace immediately after a trim.
6. **Power-up interaction.** Collect a vesicle that triggers `deleteOldestTrace()`
   while at the cap. No crash, `traceSegments` never empty.
7. Regression sweep from `AGENT_CONDUCT.md` §7.6.

## Definition of done

- [ ] Per-player cap enforced with front-trimming
- [ ] `traceSegments` can never become empty
- [ ] `MIN_TAIL_POINTS` floor protects the self-immunity window
- [ ] `trimTraceToCap` shares its removal loop with `deleteOldestTrace`
- [ ] Flat `tracePoints` / grid rebuild time demonstrated with numbers
- [ ] Gameplay impact stated in the commit message
- [ ] `docs/TASKS.md`: T07 → `DONE`, T08 → `READY`
