# T38 — Necrotic organelles: fuse, shed, and be broken apart

**Track:** K · **Depends on:** T36 (red mode must be meaningful), T37 · **Risk:** high (new hazard + new lethal entity) · **Est. diff:** ~220 lines

Read `docs/AGENT_CONDUCT.md`. This adds a **new lethal entity type**, so §4.1
(both collision paths) and §4.2 (swept only) are the traps to watch.

---

## Why the current version is invisible

Organelles were **already lethal** before T13. Read what `necrotic` changes
today: the palette, and motion (it stops drifting and becomes immovable in pair
resolution). That is all. It was lethal before, it is lethal after.

So one organelle quietly greys out every 12 seconds and nothing about how you
play changes. T13 implemented its task file faithfully — **the task file lacked a
mechanic**. This one supplies it.

---

## The mechanic (owner design, 2026-08-07)

A three-part feedback loop:

1. **Necrotic organelles fuse.** When two necrotic organelles touch, they join
   one cluster. Clusters keep absorbing any necrotic organelle that contacts them.
2. **Bigger clusters shed more debris.** A cluster periodically emits small
   lethal fragments that drift and expire. Emission rate scales with cluster
   size, so a large cluster is a genuine area-denial threat.
3. **Red mode breaks them apart, one piece at a time.** A player in
   `targetMode === 'attack'` who contacts a cluster removes **one member
   organelle**, shrinking the cluster and therefore cutting its debris rate.

The loop is the point: **neglect compounds, management pays.** Debris volume is
player-controlled, which is what stops it feeling arbitrary.

### The unifying rule this creates

After T39, red mode already shatters the protein aggregate. With this task there
is one rule covering three systems, and it belongs in the tutorial (T41) as a
single sentence:

> **Red mode breaks dead matter.**
>
> | | Lethal | Moves | Breakable in red mode |
> |---|---|---|---|
> | Living organelle | yes | drifts | no |
> | Necrotic cluster | yes | static | **yes, one piece per hit** |
> | Protein aggregate (Gen 3) | yes | static | **yes, one block per hit** |

---

## Design

### 1. Fusion is grouping, NOT merged geometry

**Do not build a compound hitbox.** Each organelle keeps the hitbox it already
has — the mitochondrion's curved spine, the lysosome's circle — and gains one
field:

```
o.clusterId = null;   // integer once it belongs to a cluster
```

Clusters are a lookup from id → member list, rebuilt or maintained as organelles
fuse. Because no hitbox changes, **`checkCollision()` and `raycast()` need no
changes at all for the cluster itself** — they already handle every member. State
that explicitly in your commit message.

Fusion detection: reuse the existing pair-resolution loop in
`updateDriftingOrganelles()`, which already computes pairwise distance. When both
are necrotic and within contact range, union their clusters.

Once clustered, members stop resolving against each other (they are one body) but
still push drifting organelles away, exactly as T37 leaves it.

### 2. Debris

New entity, new array — do **not** reuse `infection.particles`, whose lifecycle
and ownership are different.

```
let necroticDebris = [];   // { x, y, vx, vy, radius, life, maxLife }
```

- **Emission:** each cluster emits on a timer of roughly
  `DEBRIS_BASE_INTERVAL / clusterSize` seconds, from a random member's edge,
  drifting outward slowly.
- **Lethal, and short-lived.** A few seconds, then it expires. Short life is what
  makes it a *timing* hazard rather than permanent area denial.
- **Both paths (§4.1).** Insert into `rebuildSpatialGrid()` as
  `{type:'debris', raw}`; add a swept check in `checkCollision()` and a
  `'debris'` hit type in `raycast()` so bots see it. **A lethal thing the bot
  cannot see is the single most repeated mistake in this codebase.**
- **Cap it.** `DEBRIS_MAX` live at once; refuse emission at the cap. With T12's
  shrinking arena an uncapped debris field makes Gen 2 unplayable.
- Respect `ghostTimer` and `godMode` exactly as neighbouring hazards do.

### 3. Breaking a cluster

In `gameLoop`, alongside the aggregate check and modelled on it:

- Swept test of the head step against each **member** of a cluster.
- `targetMode === 'attack'` → remove that one member from `organelles` (destroy
  its sprite properly, §2), with a cooldown so one pass cannot strip a whole
  cluster in a frame. Reuse the `MASS_HIT_COOLDOWN` pattern.
- Otherwise → death, as today.
- A cluster reduced to one member is just a lone necrotic organelle again.

Emit a T17 particle burst on the break, using the **existing pooled emitter**.

### 4. Morphology — must differ from BOTH organelles and the aggregate

A fused cluster must not look like a mitochondrion, a lysosome, **or** T39's
protein aggregate. Two amorphous dead blobs on screen would be unreadable.

Gen 2 is *calcification*, so go **mineralised**:

- Grey/blue-grey, **angular and crystalline** — hard facets, straight edges,
  in deliberate contrast to the aggregate's soft amber protein lobes.
- Draw the cluster as one silhouette: union the members' outlines and suppress
  the internal boundaries so it reads as a single stone, not a pile.
- **Keep faint ghosts of the original organelle shapes inside** — a hint of
  cristae or bubbles under the mineral. It explains where the mass came from and
  ties it visually to the organelles it ate.
- Deterministic shape: seed any jitter from the member ids so it is stable frame
  to frame. Re-randomising per frame will shimmer.
- One persistent `Graphics`, redrawn from state (§4.4a: `updateX` / `drawX`
  separate). Never a `Graphics` per cluster.

### 5. Balance knobs — name them, tune them, state them

`DEBRIS_BASE_INTERVAL`, `DEBRIS_MAX`, `DEBRIS_LIFETIME`, `CLUSTER_MAX_MEMBERS`,
and the existing `NECROSIS_MAX_FRAC` / `NECROSIS_INTERVAL`. Put the chosen values
and the reasoning in `## Findings`. Gen 2 must be **harder, not hopeless** — the
membrane is already shrinking underneath all of this.

---

## Verification

1. Console clean.
2. **Gen 1 completely unaffected** — no necrosis, no fusion, no debris.
3. **Fusion happens and is visible.** At Gen 2, two necrotic organelles that
   touch become one mineralised silhouette with no internal seam. Screenshot.
4. **Debris rate scales with size.** Measure emissions per minute for a
   2-member and a 5-member cluster. The larger must be measurably higher; report
   both numbers.
5. **Breaking works and pays off.** In red mode, contact removes exactly one
   member per hit (cooldown respected), and the measured debris rate drops
   afterwards. This is the whole loop — demonstrate it end to end with numbers.
6. **Self mode still kills** on cluster contact, at the drawn edge.
7. **Debris is lethal and swept** — at Very Fast under 4× fuzzer dilation, drive
   head-on at a fragment; it must register, with no tunnelling.
8. **The bot sees debris and clusters.** 2 minutes at Gen 2: no repeated deaths
   to the same fragment or cluster. **This is the §4.1 test — do not skip it.**
9. **Caps hold.** 10 minutes at Gen 2: live debris never exceeds `DEBRIS_MAX`,
   cluster size never exceeds `CLUSTER_MAX_MEMBERS`, and the arena stays playable
   with T12's shrinking active.
10. **Visually distinct from T39.** Screenshot a Gen 3 scene containing both a
    necrotic cluster and the protein aggregate. They must be unmistakable at a
    glance. If T39 has not landed, note it and check when it does.
11. **No leak.** `worldChildren` flat over 10 minutes at Gen 2; destroyed member
    sprites are properly released.
12. Regression sweep §7.6.

## Definition of done

- [ ] Fusion implemented as clustering — **no new collision geometry**
- [ ] Debris in `spatialGrid`, `checkCollision` **and** `raycast`, swept only
- [ ] Red mode removes one member per hit, with cooldown
- [ ] Debris rate measurably scales with cluster size, and measurably falls after
      breaking — numbers in the commit message
- [ ] Mineralised crystalline look, distinct from organelles and from T39
- [ ] All caps enforced and stated in `## Findings`
- [ ] Gen 1 unchanged
- [ ] `docs/TASKS.md`: T38 → `DONE`

---

## Findings

*(Chosen constants and why; measured debris rates by cluster size and after
breaking; how the cluster silhouette is drawn.)*
