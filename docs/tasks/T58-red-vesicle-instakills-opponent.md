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

- [ ] Stable segment ids replace the array index in `isOwnNeck()`
- [ ] `i` / `segLength` either removed or made stable
- [ ] Ids reset in `startRound()`
- [ ] Reproduction no longer kills; trim and 50% wipe still work
- [ ] Self-immunity proven unchanged at every speed
- [ ] `raycast()`/`checkCollision()` still agree
- [ ] `docs/TASKS.md`: T58 → `DONE`

---

## Findings

*(What was done with `i`/`segLength`; the self-immunity evidence at each speed;
the fuzz run result.)*
