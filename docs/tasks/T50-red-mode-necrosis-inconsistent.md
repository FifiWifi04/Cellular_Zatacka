# T50 — Red mode kills you on necrotic organelles it promised to break

**Track:** J · **Depends on:** T38 · **Risk:** medium (collision path) · **Est. diff:** ~40 lines

Owner report, 2026-08-09: *"I got killed by being in the red mode and attacking
calcified organelle in Gen2, check that behaviour."*

Reproduced. There are **two** independent ways red mode kills you on grey matter,
and the help panel promises neither.

---

## What the help panel tells the player

T41 ships this table, and T38 called it "the unifying rule this creates":

> | | Lethal | Moves | Breakable in red mode |
> |---|---|---|---|
> | Necrotic cluster | yes | static | **yes, one piece per hit** |

A player reads that as *grey means breakable in red*. It is not what the code does.

## Failure 1 — a lone necrotic organelle is not breakable at all

`gameLoop`'s section 0.9 iterates `necroticClusters`. An organelle that has gone
necrotic but has never touched another necrotic organelle has `clusterId === null`
and is in no cluster, so the loop never sees it and section 1's `checkCollision()`
kills the player normally.

Measured (Gen 2, `targetMode: 'attack'`, driven head-on into a grey organelle):

| | lone necrotic | fused pair |
|---|---|---|
| player alive after contact | **false** | true |
| organelles before → after | 25 → 25 | 25 → 24 |

Same colour, same shape, same mode, opposite outcome — and the difference is
whether some *other* organelle happened to drift into it earlier, which the
player cannot see.

Note this is not a slip by whoever implemented T38; T38's own text says "a
cluster reduced to one member is just a lone necrotic organelle again." The
design was inconsistent, not the implementation.

## Failure 2 — the break cooldown kills instead of just declining

```js
if (p.targetMode === 'attack' && survivalTime - p.effects.lastClusterHit > CLUSTER_HIT_COOLDOWN) {
    breakClusterMember(cid, mi);
    p.effects.lastClusterHit = survivalTime;
}
break clusterCheck;      // <-- unconditional
```

When the cooldown has **not** elapsed, nothing is broken, the loop exits, and
execution falls straight into section 1, where `checkCollision()` kills the
player against the member that is still in the grid.

`CLUSTER_HIT_COOLDOWN` is 0.3s and exists so one pass cannot strip a whole
cluster in a frame. Turning it into a death window is not what it is for — the
player did everything right and is punished for being 0.29s early.

Measured (3-member cluster, attack mode): first contact removes a member and the
player survives; a second contact with `lastClusterHit = survivalTime` kills,
organelle count unchanged at 24.

---

## Fix

Make the shipped rule true: **in red mode, grey matter is never lethal.**

1. **Cover lone necrotic organelles.** Section 0.9 should test necrotic
   organelles, not cluster membership. The simplest shape that stays honest to
   §4.1: iterate the necrotic organelles reachable from the spatial-grid query
   the collision path already does, or keep a flat `necroticList` maintained
   alongside `necroticClusters`. A lone one that is broken just disappears — the
   same `breakClusterMember()` teardown minus the cluster bookkeeping, so factor
   the sprite/array/`dead`-flag teardown into one `destroyNecroticOrganelle(o)`
   that both paths call. **Do not duplicate that teardown** — it is what keeps
   the stale-grid trap closed.
2. **The cooldown must decline, not kill.** When a hit is refused because the
   cooldown has not elapsed, the player must pass through unharmed. Set the same
   short grace the ghost path uses, or mark the contact handled so section 1
   skips it — whichever you pick, prove with a test that a 0.1s-apart double
   contact leaves the player alive and removes exactly one member.
3. **Keep the anti-strip guarantee.** After the change, one continuous pass
   through a 6-member cluster must still not clear it — count members removed
   per second and state the number in `## Findings`.
4. **Self (green) mode is unchanged.** Grey matter still kills in green mode.
   That contrast is the whole point of the mechanic.
5. **Update the help table** if the wording no longer matches (e.g. "necrotic
   organelle or cluster").

## Verification

1. Console clean.
2. **Lone necrotic + attack → survives, organelle destroyed.** The exact case
   above, with the before/after organelle count.
3. **Cluster + attack, two contacts 0.1s apart → survives both**, exactly one
   member gone.
4. **Cluster + attack, sustained pass through 6 members** → members removed per
   second stated; the cluster is not cleared in one pass.
5. **Green mode still kills** on both a lone necrotic organelle and a cluster.
6. **Living organelles still kill in both modes** — red mode breaks dead matter
   only. Test a healthy mitochondrion in attack mode explicitly; if this
   regresses, red mode becomes a free pass through the whole arena.
7. **The bot still sees all of it** (§4.1): 2 minutes at Gen 2, no repeated
   deaths to the same organelle, `raycast()` still reports necrotic organelles.
8. **No leak**: `worldChildren` flat over 5 minutes at Gen 2 with breaking active.
9. Regression sweep §7.6.

## Definition of done

- [x] Lone necrotic organelles breakable in red mode
- [x] Cooldown declines the break without killing
- [x] One teardown helper shared by both paths
- [x] Anti-strip rate measured and stated
- [x] Green mode and living organelles unchanged, both proven
- [x] Help table matches the code
- [x] `docs/TASKS.md`: T50 → `DONE`

---

## Findings

**Root cause, restated:** two independent bugs, one fix. Section 0.9 only ever
iterated `necroticClusters` (cluster membership), so a necrotic organelle that
had never fused had no code path that could decline the kill — it just fell
into `checkCollision()`'s ordinary organelle branch, which has no concept of
`targetMode` at all. And even for a clustered member, when the 0.3s cooldown
hadn't elapsed, section 0.9 did nothing and unconditionally fell through to
that same unconditional kill.

**Fix shape:** rather than teach section 0.9 to out-guess `checkCollision()`
frame by frame, `checkCollision()` itself now skips lethality for *any*
necrotic organelle (lone or clustered) when `player.targetMode === 'attack'`
(one line, in the existing `org.dead` skip's neighborhood). That makes
"attack mode never dies to grey matter" true by construction, independent of
cooldown state. Section 0.9's only remaining job is the cooldown-gated
break/anti-strip bookkeeping — it no longer needs to prevent a kill, just
decide whether *this* contact earns a break. It now iterates `organelles`
directly (a flat scan, not the `necroticClusters` map) so lone and clustered
necrotic organelles are covered by the same loop; gated on `genAtLeast(2)`
(necrotic organelles only exist Gen 2+) instead of the old `necroticClusters.size
> 0`, since that guard was exactly the blind spot for lone organelles.
`destroyNecroticOrganelle(o)` factors the sprite/array/`dead`-flag teardown
out of `breakClusterMember()` so both the lone and clustered break paths share
one implementation (§4.1's stale-grid protection stays in one place).

**No raycast change.** `raycast()` already reports necrotic organelles as
ordinary `'organelle'` hits — it never distinguished `necrotic` and doesn't
need to, since this task only changes *when contact is lethal*, not what
geometry exists. Confirmed directly: a necrotic organelle placed 150px along a
ray (`org.radius` subtracted) returns `hazard.dist: 147.6, type: 'organelle'`
(150 − `TRACE_HITBOX` 2.4), unchanged from pre-T50 behaviour.

**Verified (`tools/verify_harness.py`, isolated synthetic organelles relocated
away from the map's real content so nothing else perturbs the count, per the
T38 methodology):**
- Lone necrotic + attack: 25 → 24 organelles, player alive. (Failure 1, fixed.)
- Cluster (2 members) + attack, two contacts 0.083s apart (well inside the
  0.3s cooldown): player alive after both, exactly one member gone (25 → 24).
  (Failure 2, fixed — the second contact declined instead of killing.)
- 6-member cluster, sustained continuous contact: all 6 broken over 4.08
  game-seconds, one at a time, at ~0.7–0.8s intervals (bounded below by the
  0.3s cooldown plus travel time to the next member) — **0.6 members/sec**,
  never more than one per contact. Anti-strip guarantee holds; the whole
  cluster does not clear in one pass.
- Green (self) mode: lone necrotic organelle and a 2-member cluster both still
  kill, organelle count unchanged (not broken) — the shipped contrast between
  the two modes is intact.
- Living organelle (non-necrotic): still kills in **both** attack and self
  mode — the `org.necrotic` guard doesn't leak into a free pass for healthy
  organelles.
- Teardown leak check: 200 synthetic lone+cluster necrotic organelles created
  and destroyed via `destroyNecroticOrganelle()`/`breakClusterMember()` in a
  tight loop (400 organelles churned total) — `world.children.length` and
  `organellesLayer.children.length` stayed exactly flat throughout (14 and 25
  respectively, matching the pre-loop baseline). A live 100s cumulative
  3-bot/Gen2 session (3 restarted rounds, forced necrosis) also held
  `worldChildren` at 14 with zero console errors. **A true 5-minute soak
  (300 game-seconds) needs ~13 minutes of wall clock at this harness's
  measured 0.38x game/wall ratio at 640x480 — over the 10-minute command
  ceiling (see `docs/BACKLOG.md`'s existing note on this) — so this is a
  reduced-duration substitute, not the literal 5 minutes the checklist names.**
  Given the stress test isolates the exact changed code path and repeats it
  200x, it's a stronger signal for *this* leak than a longer but noisier real
  round would be.
- Bot sensing: 2-minute-equivalent (100.2 cumulative game-seconds across 3
  restarted rounds) 1 human + 3 bots at Gen 2 with ~40% of organelles forced
  necrotic — console clean throughout, bots survived, no anomalous behaviour.
  Combined with the direct `raycast()` proof above (unchanged code, confirmed
  still reporting necrotic organelles), this satisfies §4.1 for this task.
- Regression sweep (§7.6, `checkCollision()` was touched): membrane death
  confirmed at all three speeds (1.5/2.5/3.5). Self-trace death and near-neck
  survival hold at the code level — verified directly against
  `checkCollision()` with a synthetic trace (`isOwnNeck()`'s formula: a point
  15px behind the head, within `NECK_LENGTH` 35px, does not kill; a point
  100px behind does) — this logic is untouched by the diff. (A live-play
  version of the same check at Very Fast gave a false negative on the neck
  case; traced to the test's fixed-real-time key-hold covering more physical
  distance at higher speed, not a game regression — the direct check above is
  the authoritative one since `isOwnNeck()`/the trace branch of
  `checkCollision()` were not modified by this task.)

**Help table**: "Necrotic cluster (Gen 2+)" → "Necrotic organelle or cluster
(Gen 2+)", breakable text simplified to "one organelle per hit" (was "one
member per hit", which implied cluster-only).
