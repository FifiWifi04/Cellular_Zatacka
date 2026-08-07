# T34 — Split-screen is choppy and stutters

**Track:** J · **Depends on:** — · **Risk:** medium

Read `docs/AGENT_CONDUCT.md`.

## The bug

> "When playing with split screen it becomes quite choppy and stuttering."

## Where to look

`updateCamera()`'s split branch renders the **whole world once per alive player**
into a per-player `RenderTexture`, then composites. With 4 players that is
**4 full world renders per frame** — bloom, trace RT sprite, particles and all —
on top of the normal pass.

Establish before changing anything, and record in `## Findings`:

1. Mean frame time in shared vs split camera, same scene, 2 and 4 players.
2. How many `app.renderer.render(...)` calls happen per frame in each mode.
3. Whether the per-player RenderTextures are re-created or resized per frame
   (T05 added `purgeSplitScreen`; confirm it is not firing every frame).
4. Whether the global bloom runs **per viewport** — if `world.filters` is set,
   each of the 4 renders pays for it separately. That alone would explain it.

## Likely fixes, cheapest first

- **Do not filter per viewport.** Move the bloom so it applies once to the
  composite (T18 already put its warning filter on `shakeRoot` for this reason).
- **Render at reduced resolution.** Each viewport is already a fraction of the
  screen; make sure its RenderTexture matches that size rather than full screen.
- **Tie split-screen cost into the quality tier** — `applyQuality()` already
  exists (T26); Low should cut viewport resolution.
- Only if still needed: skip re-rendering viewports for dead players.

## Verification

1. Console clean.
2. **Frame time before/after**, shared vs split, 2 and 4 players — eight numbers
   in the commit message.
3. Both viewports still render correctly, including during mitosis and the
   warning window.
4. No visual regression in shared mode.
5. Regression sweep §7.6.
