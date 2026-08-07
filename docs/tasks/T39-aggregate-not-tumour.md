# T39 — Replace the "tumour" with a biologically apt growth, and speed it up

**Track:** K · **Depends on:** — · **Risk:** medium

Read `docs/AGENT_CONDUCT.md`.

## The complaint

> "The tumour design looks very artificial, does not fit the rest of the
> graphics, and should be progressing faster. Plus it is not very accurate that
> it is a tumour inside of a cell — maybe it should be some other phenomenon
> which grows inside."

The owner is right on the biology. A tumour is a mass of **many cells**; it
cannot exist *inside* a single cell. Everything else in this game is a real
intracellular structure, so this one breaks the fiction.

## Rename the concept

Recommended: a **protein aggregate / aggresome** — misfolded proteins clumping
into a growing inclusion body. This is genuinely what pathological growth inside
a cell looks like, it is associated with cellular stress and ageing (fitting the
generation ladder), and it is visually distinctive.

Alternatives if you prefer: an **amyloid plaque**, a **crystalline inclusion**,
or a **stress granule** (the last is reversible, which suits a hazard that can be
broken apart).

Update every user-facing string, the roadmap wording in `Development_plan.md`
Phase 3.2, and the identifiers if the rename stays cheap — but **do not rename
`malignantMass` across the whole file if that balloons the diff**; a comment
explaining the in-game name is enough. §1.3 applies.

## Visual redesign

The current look is a hard 60 px grid of flat `0x4b3b52` squares with a
`0x1c1420` outline — literally rectangles, which is why it reads as artificial
next to the curved, glowing organelles.

Keep the **grid data model** (it makes growth, collision and shattering simple —
see T14) but stop drawing it as squares:

- Draw each block as an **irregular blob** — a few overlapping circles, or a
  jittered polygon seeded deterministically from `cx,cy` so it is stable across
  frames. Deterministic per-cell jitter is essential; re-randomising per frame
  will shimmer.
- Merge neighbours visually: skip the internal outline between two occupied
  cells so the mass reads as **one organic clump**, not a tiling.
- Match the palette and the additive-glow language of the rest of the scene —
  a sickly amber/ochre with a faint inner glow reads as "wrong protein" and sits
  next to the greens and pinks without clashing.
- Keep the bright pulse on a newly spawned block.

Still **one persistent `Graphics`**, redrawn from state — never a `Graphics` per
block (§4.4a: keep `updateX` and `drawX` separate).

## Faster growth

`MASS_GROW_INTERVAL = 10` seconds is too slow to feel like a threat. Drop it to
**~4 s**, and consider accelerating with generation (e.g. `10 - generation`,
floored at 2). Re-derive `MASS_MAX_BLOCKS` so the arena is not swallowed — with
T12's shrinking membrane the effective play area is smaller than when 40 was
chosen. State the new numbers and why.

## Must not be confusable with T38's necrotic clusters

T38 gives fused necrotic organelles a **mineralised, grey, angular/crystalline**
look. This aggregate must be unmistakably different at a glance: **soft amber
protein lobes**, rounded, warm. Both are "dead matter you can break in red mode",
so the *rule* is shared deliberately — but the player must never have to squint
to tell which is which, especially at Gen 3 when both are on screen.

If T38 has already landed, screenshot a scene containing both and check. If not,
note the constraint so T38 can check it from the other side.

## Verification

1. Console clean.
2. Screenshots before/after; the growth reads as organic and belongs to the same
   art direction as the organelles.
3. No shimmer — the per-block shape is stable frame to frame.
4. Growth rate feels like a threat within a normal Gen 3 round; state the timing.
5. Cap holds; arena stays playable at the cap **with** Gen 2 shrinking active.
6. Collision unchanged in behaviour: still swept, still in `spatialGrid`, still
   lethal in `self` and shatterable in `attack`. Bot still avoids it.
7. Every user-facing "tumour"/"malignant" string is gone.
8. Regression sweep §7.6.
