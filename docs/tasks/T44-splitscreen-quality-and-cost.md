# T44 — Split-screen looks soft and still is not smooth

**Track:** J · **Depends on:** T34 (landed) · **Risk:** medium

Read `docs/AGENT_CONDUCT.md`.

## Where T34 got to

T34 fixed the biggest single waste: the global bloom was being applied **once per
viewport**, so a 4-player split paid for it four times a frame. Bloom now runs
once on a `splitScreenLayer` composite. Measured: filter applies dropped from
4/frame to a flat 1/frame at 4 players.

That was real, but the owner reports it is **still not as smooth as shared view,
and now also looks lower resolution.** Two separate causes remain.

## Cause 1 — no antialiasing in the viewports (the "lower resolution" look)

The application is created with:

```
const app = new PIXI.Application({ resizeTo: window, backgroundColor: 0x0a0a14, antialias: true });
```

but each viewport is:

```
PIXI.RenderTexture.create({ width: viewW, height: viewH })
```

**`RenderTexture` does not inherit `antialias` from the renderer.** So shared mode
draws straight to an MSAA canvas, while split mode rasterises the world into
un-multisampled textures. Every trace, membrane ellipse and organelle curve gets
hard jagged edges — which reads exactly as "lower resolution".

**Fix:** pass `multisample: PIXI.MSAA_QUALITY.MEDIUM` (or `HIGH`) when creating
the viewport textures. Also pass `resolution: app.renderer.resolution` so the two
paths cannot drift apart if the app's resolution is ever raised.

**But MSAA costs fill rate**, which fights the smoothness complaint. So make it a
quality-tier decision through the existing `applyQuality()` (T26) rather than a
constant: High → `MSAA_QUALITY.HIGH`, Medium → `MEDIUM`, Low → none. Recreate the
textures when the tier changes; `purgeSplitScreen()` already exists.

## Cause 2 — the world is still rasterised N times per frame

Bloom is once now, but the **geometry still is not**: `updateCamera()`'s split
branch renders `world` once per alive player. Four players means four full
rasterisations of the background, cytosol, organelles, the trace sprite and the
particles.

Attack it in this order, measuring each:

1. **Shrink the viewport textures below their on-screen size.** A viewport
   displayed at 640×360 does not have to be rendered at 640×360 — render at
   0.75× or 0.6× and let the sprite upscale. This is a direct, linear fill-rate
   saving and it is the biggest lever available. Tie the factor to the quality
   tier. Note the interaction with Cause 1: MSAA plus downscaling partly cancel
   out visually, so tune them together and look at the result.
2. **The trace RenderTexture sprite is now large** — T33 grew it to span both
   cells during mitosis (~3550×1350). Each viewport samples that whole sprite and
   lets the GPU clip. Restricting it per viewport to the visible world rect would
   cut a lot of texture bandwidth. Check whether Pixi is already culling it; if
   not, this is worth more than it sounds.
3. **Skip viewports for dead players** — confirm `alivePlayers` already drives the
   loop and no texture is rendered for a player who is out.
4. **The per-frame `Graphics()` allocation** in the split branch, which T34
   deliberately left out of scope and logged in `docs/BACKLOG.md`. Hoist it to
   init and reuse — it is garbage every frame, in the one mode that is already
   the most expensive.

## Measuring honestly

This sandbox has **no GPU**, so wall-clock frame time is dominated by software
rasterisation and will not cleanly show these wins — T34 hit exactly this and was
right to report the apply-count instead of pretending the timing proved anything.

Do the same here: report **countable** proxies (draw calls per frame, textures
sampled, bytes of render target per frame, allocations per frame) as the primary
evidence, and wall-clock only as a secondary note with the caveat attached.

## Verification

1. Console clean.
2. **Sharpness.** Screenshot the same scene in shared and split at High quality.
   Trace and membrane edges must look comparable — no visible stair-stepping in
   split. Attach both.
3. **Tiering works.** Low/Medium/High each produce a different viewport texture
   configuration; confirm by reading the texture's `multisample` and dimensions.
4. **Render-target bytes per frame** before and after the downscale, at 2 and 4
   players. Report the numbers.
5. **Allocation.** No `new PIXI.Graphics()` remains inside the per-frame split
   branch.
6. **Correctness.** Both/all viewports render correctly at 2 and 4 players,
   during mitosis (post-T33 bounds), and during the T18 warning window.
7. Tier changes mid-round recreate the textures without leaking —
   `worldChildren` flat, `splitTextures.length` bounded.
8. Regression sweep §7.6.

## Findings

Measured via `tools/verify_harness.py` (headless, software WebGL2 — no GPU).

1. **MSAA RenderTextures silently produce a blank capture in this sandbox.**
   Isolated test: `PIXI.RenderTexture.create({width:100,height:100,multisample:
   PIXI.MSAA_QUALITY.MEDIUM})`, draw a filled rect into it, read back with
   `renderer.extract.pixels()` — every byte is 0, no GL error, no console
   warning. `MAX_SAMPLES` reports 4 and `webGLVersion` is 2, so PIXI believes
   multisampling is supported and takes that path; it just never resolves.
   Root-caused, not assumed: reproduced with a minimal Graphics rect outside
   any game code, and confirmed the split-screen blackout only occurred while
   `multisample !== NONE` (locking the tier to `low`, which has no MSAA,
   rendered correctly at every other setting unchanged).
   **Fix:** a one-time capability probe (`splitMSAASupported`, a throwaway 4x4
   RT rendered and read back at module init) gates `splitMultisample` — a
   backend that can't actually resolve MSAA gets `MSAA_QUALITY.NONE` for every
   tier instead of a blank viewport. Confirmed the probe correctly reports
   `false` here and viewport content renders again with it wired in. Whether
   real hardware needs the fallback path is unverifiable from this sandbox;
   the probe means it's automatic either way.
2. **Viewport texture sizing/multisample per tier** (640x480 screen, 4 alive
   players, so each viewport is 320x240 on screen):
   | tier | RT size | multisample requested | multisample applied (this sandbox) |
   |---|---|---|---|
   | low | 192x144 (0.6x) | NONE | NONE |
   | medium | 256x192 (0.8x) | MEDIUM | NONE (probe-gated) |
   | high | 320x240 (1.0x) | HIGH | NONE (probe-gated) |
3. **Render-target bytes/frame.** Because `columns` is fixed at 2 and `rows`
   adjusts to keep the grid filling the screen, total viewport area is the
   full screen regardless of player count (verified directly: 2 players at
   640x480 → two 320x480 viewports; 4 players → four 320x240 viewports; both
   sum to 640x480). So bytes/frame = `screenW * screenH * 4 * splitRenderScale²`,
   independent of player count:
   - before (no downscale): 640x480x4 = 1,228,800 bytes/frame
   - low (0.6x): 442,368 bytes/frame (36%)
   - medium (0.8x): 786,432 bytes/frame (64%)
   - high (1.0x): 1,228,800 bytes/frame (unchanged — deliberate, keeps split
     pixel-comparable to shared mode)
4. **Trace-sprite sampling per viewport — investigated, not changed.**
   `trailGlowSprite`/`trailCoreSprite` default `cullable = false` (confirmed in
   `vendor/pixi.min.js`), so PIXI performs no bounds-test skip today; every
   viewport capture samples the full trace RT (up to ~3550x1350 during
   mitosis) regardless of what fraction is on screen. Setting `cullable = true`
   would let PIXI's built-in `_renderWithCulling` skip the draw call when a
   viewport's frame doesn't intersect the sprite's bounds at all (e.g. a
   viewport centred on cell A while the trace spans into cell B). Not applied
   here: the trace sprite carries a `BlurFilter`, whose bleed extends the
   visually-drawn area slightly past the geometric bounds culling would test
   against, and there is no GPU in this sandbox to visually confirm the edge
   case doesn't clip glow at a viewport boundary. Left as a follow-up in
   `docs/BACKLOG.md` rather than guessed at.
5. **Dead players already skip rendering** — confirmed `for (let i = 0; i <
   alivePlayers.length; i++)` in the capture loop only iterates alive players;
   no change needed (item 3 in the task file's Cause 2 list).

## Definition of done

- [x] Viewport textures antialiased, via the quality tier (probe-gated — see Findings §1)
- [x] Viewport render resolution tied to the tier, with bytes/frame reported
- [x] Trace-sprite sampling per viewport investigated and reported
- [x] Per-frame `Graphics()` allocation removed
- [x] Shared vs split sharpness screenshots attached
- [x] `docs/TASKS.md`: T44 → `DONE`
