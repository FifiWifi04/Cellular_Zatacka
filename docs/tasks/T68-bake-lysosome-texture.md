# T68 — Bake the lysosome to a texture, behind a flag

**Track:** M (Phase 2, unparked) · **Depends on:** — · **Risk:** medium (rendering path) · **Est. diff:** ~120 lines

Read [`docs/PHASE2-ASSET-PIPELINE-PLAN.md`](../PHASE2-ASSET-PIPELINE-PLAN.md)
and [`tasks/P01-asset-pipeline-parked.md`](P01-asset-pipeline-parked.md) before
starting. This is the first attempt at the pipeline since it was parked, and it
is deliberately the smallest possible one.

**This task ends with the owner looking at a screenshot.** T69 and T70 stay
`BLOCKED` until they do. Do not start them.

---

## What this is, and what it is not

**It is** a rendering-path change: draw lysosomes from a `PIXI.Texture` instead
of a per-organelle `PIXI.Graphics`.

**It is not** new artwork. The texture is baked from
`createOrganelleGraphics()` — the drawing the game already ships — rendered once
into a `RenderTexture` at round start. The output should be **pixel-comparable
to today**. That is the point: it isolates the pipeline from the art question
that sank the first attempt, and it gives an objective success test instead of
an opinion.

**Do not load any `.jpg` from the repo.** Those four files are photographs in the
wrong format and they are what made this fail last time.

## Design

1. **Bake once per round, per variant.** A lysosome has a normal and a
   `necrotic` palette (T13), so that is two textures, not one. Build them in
   `generateMap()` where the round's other one-time setup lives, and destroy
   them with the rest of it (§2 PixiJS lifecycle — a leaked `RenderTexture` is
   the most expensive kind).
2. **Bake at the largest size actually drawn**, then scale the sprite down.
   Baking small and scaling up is how the first attempt got soft edges.
3. **Await the texture before the first draw.** `RenderTexture` from a
   `Graphics` is synchronous, which is precisely why this route avoids P01's
   async trap — but assert it, do not assume: if the texture is not `valid`
   before the first sprite is created, fall back to the vector path for that
   frame rather than drawing a 1×1.
4. **Flag it.** `USE_BAKED_ORGANELLE_TEXTURES`, default **off**. Both paths must
   work in the same build so they can be screenshotted back to back. This flag is
   also the revert if the measurement in T70 disappoints.
5. **Touch nothing else.** `organelles[]`, the spatial grid, `checkCollision()`,
   `raycast()`, radii — all unchanged. The lysosome hitbox is a plain radius, so
   there is no geometry to reconcile. **If you find yourself editing a hitbox,
   stop** (§4.4).

## Verification

1. Console clean.
2. **Screenshot diff, flag off vs flag on**, same seed, same frame, at
   `world.scale.x` ≈ 0.6 and ≈ 2.0. Differences must be imperceptible. State
   what differs if anything does — a small difference honestly reported is fine;
   a claim of "identical" that is not is not.
3. Necrotic lysosomes correct too (both variants baked) — screenshot at Gen 2.
4. **Collision unchanged**: drive head-on into a lysosome at Very Fast under 4×
   fuzzer dilation, flag on and off, and report the same death time.
5. **No leak**: `worldChildren` and texture count flat over 10 minutes, across at
   least 3 rounds and one mitosis (which rebuilds the map).
6. Quality tiers still respected.
7. Regression sweep §7.6.
8. **Do not update T69/T70 to `READY`.** Leave them `BLOCKED` — the owner gate
   is a human step. Say in `## Findings` that the screenshots are ready to look at.

## Definition of done

- [ ] Lysosome drawn from a baked texture behind `USE_BAKED_ORGANELLE_TEXTURES`
- [ ] Both palettes baked; textures destroyed with the round
- [ ] Screenshot diff at two zooms, flag on vs off
- [ ] Collision proven identical
- [ ] No texture or display-object leak across rounds and a mitosis
- [ ] T69/T70 left `BLOCKED`
- [ ] `docs/TASKS.md`: T68 → `DONE`

---

## Findings

*(The screenshot pairs, any visible difference, the collision timings, the leak
numbers.)*
