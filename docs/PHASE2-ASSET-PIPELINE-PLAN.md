# Phase 2 (unparked) — the asset pipeline, replanned

Owner, 2026-08-14: *"can we plan for the upgrades that were parked for now? I
want to run another routine in coming days."*

This unparks **P01**, the sprite/asset substitution parked on 2026-08-03 after
the first attempt looked wrong. Read
[`tasks/P01-asset-pipeline-parked.md`](tasks/P01-asset-pipeline-parked.md) first
— it records what was tried and why it failed, and none of that has changed.

---

## The thing that has to be said before any of this is scheduled

**The parked attempt conflated two different goals**, and a routine cannot
deliver them both:

| | goal | can an agent do it? |
|---|---|---|
| A | **Sprite rendering pipeline** — draw organelles from textures instead of `PIXI.Graphics` every frame | **Yes.** It is mechanical: texture creation, lifecycle, batching, hitbox fidelity. Fully verifiable. |
| B | **Better-looking organelles** | **No.** This is art direction. An agent cannot author artwork, and the four `.jpg` files in the repo are photographs — the wrong thing in the wrong format. |

The original attempt failed at **B** and got blamed on **A**. Worse, it damaged
the game reaching for B: it set `bendY = 0` to make the mitochondrion's curved
spine match a rectangular sprite — changing the *physics* to fit the *art*.

So the plan below is **A only**, with B left as an explicit owner decision.

### And the case for B has weakened considerably since parking

P01 predicted this: *"If T21 lands and looks good, that is also evidence about
this parked task."* Since then **T21** (additive blending), **T56** (the trace
lattice) and all six sections of **T62** have landed on the vector renderer —
membrane low-zoom treatment, parallax, edge falloff, cytosol detail, breathing.
The nucleus/ER/Golgi cluster and the mitochondria now read well at playing zoom,
which is exactly what the sprite swap was originally supposed to buy.

**My recommendation: do not schedule T68–T70 to make the game prettier.**
Schedule them only if you want the *performance and consistency* of a texture
pipeline. If what you actually want is nicer organelles, the cheaper path is to
commission or generate art and hand it over as a separate step — the pipeline
does not have to come first.

---

## What the routine can safely build

### T68 — Bake the existing vector art to textures (no new artwork)

**The key insight that makes this schedulable at all:** the game already has good
organelle art — it is drawn by `createOrganelleGraphics()`. Render *that* into a
`RenderTexture` once per organelle type at round start, then draw sprites.

This gets the whole pipeline — texture creation, sizing, lifecycle, sprite
swap, hitbox fidelity — with **zero art risk**, because the output is
pixel-comparable to what ships today. If it looks different, that is a bug, and
that is a far better test than "does this photo look nice".

- One type first: **lysosomes** (circle, rotation-invariant, hitbox is a plain
  radius — no geometry conflict possible).
- Keep `createOrganelleGraphics()` intact behind a flag so vector and sprite
  render side by side in the same build.
- Success criterion is **a screenshot diff**, not an opinion.

### T69 — Extend to mitochondria, correctly

The hard case, and the one that broke last time. The hitbox is a 5-segment
quadratic spine from `radius`, `bendY` and `rotation`.

**The rule, non-negotiable: never change a hitbox to match a sprite.** If they
disagree, the sprite is wrong. Baking from the existing vector drawing sidesteps
this entirely, since the drawing already follows the spine.

### T70 — Vesicles, virus, and a measurement

Finish the set, then answer the question that justifies the whole exercise:
**does it actually run faster?** Draw-call count and frame cost, four players,
Gen 3, against the vector build. If it is not measurably better, say so — that
is a legitimate result and the flag from T68 makes reverting trivial.

### T71 (owner-gated, not for a routine) — real artwork

Only if you decide you want it. The requirements P01 recorded still hold, and
they are requirements on the *art*, not the code:

- **PNG or WebP with real alpha.** Not JPEG — no alpha, and compression
  artefacts become visible halos under additive blending.
- **Authored for additive blending**: black background, bright emissive subject.
  A mid-tone photograph washes out. This was the most likely cause of "did not
  look right".
- **Sized to their drawn dimensions**, not 0.5–0.8 MB each.
- **Mitochondrion art must follow the curved spine**, or it does not get used.

The four existing `.jpg` files fail every one of these. Do not delete them, but
do not expect them to work either.

---

## Order and gating

```
T68 (lysosome, baked from vector, flagged)
      │
      └── OWNER LOOKS AT IT ← the gate that was missing last time
              │
              ├── looks identical → T69 → T70 → measure → keep or revert on the flag
              └── looks worse     → stop, flag off, re-park. One session lost.
```

That gate is the whole lesson from P01. The first attempt went all the way to
four organelle types and a physics change before anyone looked.

## For the routine specifically

- These are **sequential** and T69/T70 must stay `BLOCKED` until you have looked
  at T68. A routine left to itself will happily do all three.
- T68 is the only one that should be `READY` when you start the routine.
- If a session finds itself wanting to change a hitbox, a collision constant, or
  `bendY`, that session has gone wrong — **stop and report** (`AGENT_CONDUCT.md`
  §4.4).
