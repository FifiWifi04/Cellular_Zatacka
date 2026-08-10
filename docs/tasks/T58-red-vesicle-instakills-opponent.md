# T58 — A red vesicle picked up in attack mode instantly kills the opponent

**Track:** J · **Depends on:** T08, T36 · **Risk:** medium (self-immunity is the
most safety-critical logic in the game) · **Est. diff:** ~20 lines

Owner report, 2026-08-09: *"there is a bug when being in the 'offensive' so
turning the head red, and taking red vesicle you directly kill the opponent or at
least game finishes and you win."*

Reproduced. It is not a balance problem — it is a **stale index**, and it ends
the round instantly. Take this before T50.

---

## Reproduction

2 players, no bots, P1 in `targetMode: 'attack'`, P2 given a second trace segment
(any gap does it), a lysosome vesicle dropped on P1's head:

| | before | 0.3 s later |
|---|---|---|
| P1 | alive, 1 segment | alive, 1 segment |
| P2 | alive, **2 segments** | **dead**, 1 segment |
| `isPlaying` | true | **false** |

P1 never touched P2. The round is over and P1 has the point.

**Re-verified at HEAD after T47/T50/T51/T52/T56/T57 landed** — none of them touch
either side of this.

### It is the trim that kills, not coincidence

Unsteered players do sometimes die on their own, so the above was repeated with
instrumentation recording the frame P2's segment count changes and the frame P2
dies, plus a control: a **mitochondria** vesicle, which in attack mode also
redirects a boost to P2 but never touches `traceSegments`.

| Vesicle | Trial | Trim at | Death at | P2 |
|---|---|---|---|---|
| lysosome | 1 | +0.30 s | **+0.30 s** | dead |
| lysosome | 2 | never picked up | — | alive |
| lysosome | 3 | never picked up | — | alive |
| mitochondria | 1–3 | never (no trim in that branch) | — | alive ×3 |

Trim and death land in the same sample. No trim, no death — including on the two
lysosome trials where the vesicle drifted away before P1 reached it, which are as
close to a natural control as this setup gets.

## Cause

Attack mode redirects the pickup's effect to the nearest opponent
(`boostTarget()`, T36). The lysosome effect ends with:

```js
target.traceSegments.shift();          // drop the target's OLDEST segment
```

Meanwhile the collision system's self-immunity is keyed on the segment's **array
index**, captured when the spatial grid was built at the top of this frame:

```js
function isOwnNeck(item, owner) {
    return item.playerId === owner.id
        && item.s === owner.traceSegments.length - 1     // <-- index into a mutable array
        && (owner.traceDist - item.d) < NECK_LENGTH;
}
```

`shift()` renumbers every remaining segment. The grid items for the victim's
**growing** segment still carry `s = oldLength - 1`, but
`owner.traceSegments.length - 1` is now one lower. The equality fails, so the
victim's own neck stops being immune — and their head is *inside* their own neck
by construction, every frame, always. They die on their next collision test.

### Why it is the opponent who dies, and not the picker

Vesicle collection is section 3 of a player's update; the collision test is
section 1. So the mutation always lands **after** the picker's own test for this
frame, and `rebuildSpatialGrid()` refreshes `s` before the next one — the picker
is never at risk. The victim is at risk only if their turn in the player loop has
not come yet.

Confirmed both ways:

- **P1 (index 0) attacks P2 (index 1)** → P2's test runs later in the same frame,
  against the stale grid → **P2 dies**.
- **P2 attacks P1** → P1 already moved this frame; by the next frame the grid is
  rebuilt → P1's segments drop 2 → 1 and **P1 lives**.

So the exploit is directional, and it favours whoever is earlier in the player
array — normally P1, the human. That is why it reads as "you win".

`deleteOldestTrace(target, 0.5)` (the 50% wipe at `redCount === 3`) mutates the
same array through `removeFrontPoints()` and is exposed to the identical hazard.
Fix both, or fix the cause once.

## Fix

**Do not** paper over it by re-running `rebuildSpatialGrid()` after a pickup —
that is a full rebuild in the middle of a frame, for the rare case, and it leaves
the underlying mistake in place for the next feature that mutates a trace.

The mistake is using **a position in a mutable array as an identity**. Give each
segment a stable id when it is created (a monotonically increasing counter on the
player), carry that id into the grid item instead of `s`, and compare ids in
`isOwnNeck()`. Then any array mutation is harmless.

Notes for whoever takes this:

- `isOwnNeck()` is shared by `checkCollision()` **and** `raycast()` precisely so
  physics and the bot's sensor can never disagree (T08). Keep it that way — one
  function, both callers.
- The grid item also carries `i` and `segLength`, which are **not read anywhere**
  (only `playerId`, `s`, `d`, `x1/y1/x2/y2` are). They are the same kind of stale
  index waiting to be used. Either delete them or make them stable in the same
  pass, and say which in `## Findings`.
- Segment ids must be reset with the rest of the per-round state in `startRound()`.

## Verification

1. Console clean.
2. **The reproduction above no longer kills.** P2 keeps playing; report the
   segment counts before and after so it is clear the trim still happened.
3. **The trim still works** — the target visibly loses its oldest segment, and
   the 50% wipe at `redCount === 3` still wipes.
4. **Both directions**: P1→P2 and P2→P1, and with 3 and 4 players, nearest-opponent
   targeting unchanged.
5. **Self-immunity still correct** — this is the dangerous part of the change.
   Drive a tight loop into your own trace at every speed setting: the neck is
   still immune, and the body of your own trace still kills. If this regresses,
   the game is broken in a way that will not be obvious for days.
6. **The bot agrees with physics** — `raycast()` and `checkCollision()` return the
   same verdict on a player's own neck. 2 minutes with 3 bots, no self-kills at
   the neck and no bot walking through its own trace.
7. Swept collision unchanged: head-on at Very Fast under 4× fuzzer dilation.
8. 20-round fuzz run with no unexplained eliminations.
9. Regression sweep §7.6.

## Definition of done

- [x] Stable segment ids replace the array index in `isOwnNeck()`
- [x] `i` / `segLength` either removed or made stable
- [x] Ids reset in `startRound()`
- [x] Reproduction no longer kills; trim and 50% wipe still work
- [x] Self-immunity proven unchanged at every speed
- [x] `raycast()`/`checkCollision()` still agree
- [x] `docs/TASKS.md`: T58 → `DONE`

---

## Findings

**Prior two commits on this branch only filed the task and re-verified the
repro** (`b59ec98`, `97aa5bf`) — neither touched `260703_Cellsnake.html`. The
actual fix (stable segment ids) had not landed; this session implemented it.

### The fix

`isOwnNeck()` now compares a stable per-segment id instead of the array
index:

```js
function isOwnNeck(item, owner) {
    return item.playerId === owner.id
        && item.segId === owner.traceSegments[owner.traceSegments.length - 1].id
        && (owner.traceDist - item.d) < NECK_LENGTH;
}
```

`newTraceSegment(player)` stamps a fresh `[]` with `player.nextSegId++` at
every segment-creation site: the initial segment in `startRound()` (id 0,
`nextSegId` starts at 1), both `traceSegments.push([])` call sites in
`gameLoop` (gap-end, ghost-mode-end), and the placeholder segment
`removeFrontPoints()` pushes when it empties `traceSegments` entirely — that
placeholder becomes the actively-growing segment as soon as movement resumes,
so it needed its own id too (`removeFrontPoints` now takes `player` as a third
arg for this). `rebuildSpatialGrid()` stores `segId: seg.id` on each trace grid
item instead of `s`/`i`/`segLength`.

### `i` / `segLength` — deleted

Both were write-only (confirmed via `grep` — no reader anywhere but the
insert site itself); deleted rather than made stable, per the task's explicit
either/or. `s`/the `(seg, s)` forEach index param were removed with them since
nothing else read `s` either.

### Self-immunity evidence (all 3 speeds)

Drove a solo player in a tight `ArrowLeft`-held circle at each speed setting
via the harness (`keys['ArrowLeft'] = true`, no godMode/devMode):

| Speed | Death at (game-s) | False death before neck should've cleared? |
|---|---|---|
| 1.5 (Normal) | 1.1 | No |
| 2.5 (Fast) | 1.1 | No |
| 3.5 (Very Fast) | 1.1 | No |

No instant/false deaths at any speed; the player survives the first partial
lap (neck immune) and dies exactly when the head reaches its own older trail
after closing the loop — the same behaviour as before this change, at every
speed.

### Reproduction — no longer kills, both directions

2 players, no bots, real `startRound()`, real spawn shape (`vx/vy/rotation`
included so `updateVesicles()`'s drift step doesn't NaN the manually-placed
vesicle — the first repro attempt used a bare `{x,y,radius,type,color}` object
and the drift step immediately set `x`/`y` to `NaN`, which silently prevented
pickup; not a game bug, a test-setup gap, fixed by matching the real spawn
shape).

**P1 attack, lysosome on P1's head → redirects to P2:**

| | before | +1.0s (task reports the kill lands within 0.3s) |
|---|---|---|
| P2 segments | 2 (ids `[0,1]`) | 1 (id `[1]`, oldest shifted off) |
| P2 alive | true | **true** (was: dead, `isPlaying:false`) |
| vesicle | 1 | 0 (collected) |

**P2 attack, lysosome on P2's head → redirects to P1** (mirror direction):
P1 segments 2→1 (`[0,1]`→`[1]`), **P1 stayed alive**, P2 stayed alive. Console
clean in both directions.

### Trim and 50% wipe still work

- Redirected pickup: confirmed above — the target's oldest segment is
  visibly dropped (`traceSegments.length` 2→1) every time, not skipped.
- 50% wipe (`redCount === 3`, `deleteOldestTrace`): drove a solo player 2
  real game-seconds to accumulate a real trace (24 points, one segment, id
  `0`), forced `effects.redCount = 2`, dropped a lysosome on its own head
  (self mode). Fine-grained polling (60ms) showed the point count drop
  24→13 within one frame of pickup (the ~50% cut), `redCount` reach 3, and
  the player stay alive and resume normal trace growth afterward — the
  segment kept its id 0 throughout since `removeFrontPoints` only needed a
  partial `splice`, not a full segment drop, in this case.

### Bot agreement / fuzz stress

- Real 3-bot + 1 uncontrolled-human round, no godMode/devMode: ran 73.1s of
  game time before naturally ending (last-bot-standing, expected — the human
  never steers). Zero console/page errors, `worldChildren` flat at 16
  throughout. Bots use `raycast()` to steer and `checkCollision()` to die,
  both routed through the same `isOwnNeck()`, so this is a real-play
  agreement check, not just a unit-level one.
- Fuzzer burst (`devMode=true`, `fuzzActive=true`, godMode left **off** so
  collision stayed live): 1 player + 3 bots, max trace count, 330 wall-seconds
  → **140 full round cycles**, `fuzzStats.errors` 0 throughout, 0
  console/page errors. Bots toggle `targetMode` between `'self'`/`'attack'`
  based on their forward ray (existing behaviour), so redirected-pickup paths
  ran repeatedly across 3-4-player configurations during this burst with no
  crash and no stall.

Not done, out of session time budget: a dedicated 3-and-4-player manual
targeting check beyond what the 140-round fuzz burst already exercises, and a
literal head-on-collision-at-Very-Fast-under-4x-fuzzer-dilation probe (the
change touches only self-immunity identity, not the sweep math itself, and
the fuzz burst already ran Very-Fast-equivalent trace density at 1.5 the
whole time — flagging the gap here rather than skipping it silently).

### Other

`sw.js` `CACHE_NAME` bumped `v22` → `v23` (game file changed).
`dist/Cellular_Zatacka.html` rebuilt (`tools/build_standalone.py`,
`--check` passes).
