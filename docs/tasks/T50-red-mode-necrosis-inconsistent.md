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

- [ ] Lone necrotic organelles breakable in red mode
- [ ] Cooldown declines the break without killing
- [ ] One teardown helper shared by both paths
- [ ] Anti-strip rate measured and stated
- [ ] Green mode and living organelles unchanged, both proven
- [ ] Help table matches the code
- [ ] `docs/TASKS.md`: T50 → `DONE`

---

## Findings

*(Removal rate per pass, the shape chosen for the necrotic lookup, and why.)*
