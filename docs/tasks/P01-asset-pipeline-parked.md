# P01 — Phase 2: asset pipeline & sprite substitution — **PARKED**

**Status:** `PARKED` by owner decision. **Do not implement.** This file exists to
record what was tried, why it was parked, and what a future attempt must handle.

---

## Owner decision

> "Substitution of vector drawn organelles with images did not work well so for
> now I would like to skip it. Maybe need to figure out a better way to do it."

A coding agent must **not** pick this up from the board. If a task file appears to
require sprite substitution, that task is mis-scoped — stop and report.

---

## What the roadmap asks for

`Development_plan.md` Phase 2:

> 2.1 Refactor rendering engine to load 2D pre-rendered image files (.png/.webp)
> instead of drawing vector shapes via `PIXI.Graphics`. Swap primitives for
> sprites: Organelles, Viruses, Vesicles, and the outer Membrane.
>
> 2.2 Apply Additive Blending to player head cores, active traces, and vesicle
> drop zones.

---

## State of the repository

- `walkthrough.md` describes Phase 2 as **complete** — base64-embedded textures
  (`base64Mito`, `base64Lyso`, `base64Virus`, `base64Vesicle`), `PIXI.Texture.from`
  loads, sprite swaps, and a `baseTexture.valid` async-scaling workaround.
- **None of that is in `260703_Cellsnake.html` at commit `4bf057f`.** There are
  zero occurrences of `base64`, `Texture.from`, `.jpg`, or `Assets`. Organelles
  are still drawn by `createOrganelleGraphics()`. The only `PIXI.Sprite` in the
  file is the split-screen `RenderTexture` in `updateCamera()`.
- `mitochondria.jpg`, `lysosome.jpg`, `virus.jpg`, `vesicle.jpg` are present in
  the repo (0.5–0.8 MB each) and are referenced by **nothing**.
- The mitosis-related fixes described in the same `walkthrough.md` **are** present
  (`window.golgiData` persistence, precise Golgi shatter coordinates, the nucleus
  visibility toggle and its 15-vesicle burst).

So the file is the pre-asset-swap version with the mitosis fixes applied. Treat
`walkthrough.md`'s Phase 2 section as **describing a reverted or lost attempt**,
not current behaviour.

**Do not delete the `.jpg` files** — they are the source assets for a future
attempt.

---

## Why it did not work — what a future attempt must solve

Recorded from the attempt and from what the current code implies:

1. **Async texture sizing.** Setting `.width`/`.height` before a texture loads
   makes PixiJS scale against a 1×1 base texture, producing enormous sprites.
   `walkthrough.md` documents the `baseTexture.valid` + `'update'` listener
   workaround; any future attempt needs it, or should use `PIXI.Assets.load` with
   an await before the first draw.

2. **Hitbox/sprite desync — the real risk.** The mitochondrion hitbox is a
   5-segment quadratic spine derived from `radius`, `bendY`, and `rotation`. A
   rectangular sprite does not match that shape. The previous attempt "solved" it
   by setting `bendY = 0` to straighten the physics to match a straight sprite —
   i.e. it changed the *physics* to fit the *art*. That is backwards
   (`AGENT_CONDUCT.md` §4.4) and it flattens a deliberate piece of the game's
   feel.

   A correct approach keeps the curved spine authoritative and either
   (a) commissions art that matches the spine, or (b) draws the sprite along the
   spine as a rope/mesh, or (c) accepts a straight spine as an explicit,
   owner-approved gameplay change — not as a rendering side effect.

3. **Additive blending vs. photographic source art.** `BLEND_MODES.ADD` was used
   so the dark JPEG backgrounds would blend away. That works for glow but makes
   any mid-tone in the source art wash out, which is a plausible cause of "did not
   work well". Assets for additive blending need to be authored for it: black
   background, bright emissive subject, and ideally PNG with real alpha rather
   than JPEG.

4. **JPEG is the wrong format here.** No alpha channel, and compression artefacts
   around bright edges become visible halos under additive blending. PNG or WebP
   with alpha, at the size actually drawn.

5. **File size.** ~2.6 MB of JPEG, and base64 inflates it by ~33%. Embedding all
   four as data URIs adds ~3.5 MB to a single HTML file. Workable but heavy; worth
   downscaling the source art to the drawn size first.

---

## Recommended shape of a future attempt

Not a task — a sketch for whoever re-plans this.

1. **Do one organelle type first**, end to end, and look at it before touching
   anything else. Lysosomes are the easy case (a circle, rotation-invariant,
   hitbox is a plain radius). If lysosome sprites do not look better than the
   vector version, the problem is the art direction, not the code.
2. **Never change a hitbox to match a sprite.** If they disagree, the sprite is
   wrong.
3. Keep `createOrganelleGraphics()` intact behind a flag during the transition, so
   vector and sprite rendering can be compared side by side in the same build.
4. Author assets for additive blending: black background, bright emissive
   subject, PNG with alpha, sized to their drawn dimensions.
5. Phase 2.2 (additive blending) is **not parked** — it is independent of the
   asset swap and is written up as **[T21](T21-additive-blending.md)**, working on
   the current vector renderer. Note that 2.2's three literal targets (player head
   cores, active traces, vesicle drop zones) are already satisfied: heads and
   traces are drawn into the additive `trailGlow`/`trailCore`, and the Golgi
   cisternae carry `BLEND_MODES.ADD`. T21 extends the look to organelles, vesicles
   and the virus.

   If T21 lands and looks good, that is also **evidence about this parked task**:
   it isolates how much of the intended bioluminescent aesthetic comes from
   blending rather than from the artwork. If the vector renderer looks right with
   additive blending alone, the case for the asset swap weakens considerably.

---

## Also worth fixing when this is revisited

`walkthrough.md` currently documents Phase 2 as delivered, which is misleading for
anyone reading the repo. Either annotate it as describing a reverted attempt, or
move its Phase 2 section into this file. **This is not a coding-agent decision** —
leave it to the owner.
