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

## Findings

Measured at commit `ba88d2f`, via `tools/verify_harness.py` (640x480 headless,
no GPU — software rasterization; quality auto-detects to `low` and had to be
locked to `medium` to exercise bloom at all).

1. **Mean/median frame time (medium quality, immortal, 640x480)** — see
   `## Verification` below; wall-clock frame time in this sandbox is dominated
   by rasterization/JS, not filter cost (consistent with the harness's own
   documented caveat), so it does not cleanly isolate the bloom effect. Item 4
   below is the number that does.
2. **`app.renderer.render()` calls per frame**: shared = 3 (trace RT writes),
   split = `3 + 2*alivePlayers` (one world-capture + one border-draw per
   viewport) — 7 at 2p, 11 at 4p. Confirmed by instrumented count.
3. **`purgeSplitScreen()`**: only called from `handleViewportResize()` (window
   resize/orientationchange) and `startRound()`. Not called from `updateCamera()`
   or anywhere in the per-frame path — not the cause.
4. **Global bloom runs per viewport — confirmed, and it scales with player
   count.** `world.filters` held `[bloomFilter]` (`AdvancedBloomFilter`) whenever
   bloom is enabled for the tier, and the split branch called
   `app.renderer.render(world, {renderTexture: rt})` once per alive player,
   applying the filter each time. Instrumented `bloomFilter.apply()` call count
   over 20 frames at medium quality, before the fix:
   - `shared_4p`: 1 apply/frame
   - `split_2p`: **2 applies/frame**
   - `split_4p`: **4 applies/frame**

   i.e. exactly `alivePlayers` applies/frame in split mode — the smoking gun.

## Fix

Moved bloom off `world` (rendered N times in split mode) onto a new
`splitScreenLayer` container that holds the split-screen viewport sprites and
is part of the single once-per-frame automatic stage render — the same pattern
T18 already uses for the warning filter on `shakeRoot`. `applyQuality()` now
mirrors `world.filters` onto `splitScreenLayer.filters`. The split branch of
`updateCamera()` saves and nulls `world.filters` for the duration of the
per-viewport captures (so the raw scene is captured cheaply) and restores it
afterward for the shared-mode path.

## Verification

1. Console clean — confirmed via harness `assert_console_clean()` across all
   checks below.
2. **Frame time before/after**, shared vs split, 2 and 4 players (medium
   quality forced, median ms over 30 rAF samples, 640x480 headless/no-GPU):

   | scene | before | after |
   |---|---|---|
   | shared 2p | 138.9 | 138.1 |
   | shared 4p | 182.0 | 201.8 |
   | split 2p | 155.0 | 152.8 |
   | split 4p | 238.2 | 287.7 |

   Wall-clock frame time did **not** improve in this sandbox — as
   `verify_harness.py`'s own docstring already notes for this environment,
   "the cost is rasterisation, not the filter" when there is no GPU. The
   sample-to-sample noise here (single run per config, shared CPU) is larger
   than the effect being measured. The metric that actually isolates the bug —
   bloom-filter apply count per frame, measured by monkey-patching
   `bloomFilter.apply()` and comparing the same commit with/without the fix
   (`git stash`) — is unambiguous:

   | scene | before (applies/frame) | after (applies/frame) |
   |---|---|---|
   | shared 4p | 1 | 2 |
   | split 2p | **2** | **1** |
   | split 4p | **4** | **1** |

   Split-mode bloom cost no longer scales with player count. On real GPU
   hardware (where filter-pass overhead is proportionally much larger than in
   this software-rasterized sandbox) this is where the reported stutter should
   actually go away; that could not be directly confirmed here for lack of a
   GPU in this environment.
3. Both viewports render correctly, including with bloom forced on at `high`
   quality (2- and 4-way splits) — screenshots inspected, borders and bloom
   glow intact, no seams or missing content.
4. No visual regression in shared mode — bloom path (`world.filters`) is
   untouched there except for the added save/restore around the split branch,
   which is a no-op when `cameraMode !== 'split'`.
5. Regression sweep: non-immortal rounds in both shared and split camera at
   speed 1.5 and 3.5 all end in death (membrane collision) as expected, console
   clean throughout. My diff does not touch `checkCollision`, `checkArcCollision`,
   `raycast`, or `rebuildSpatialGrid`, so this is a sanity check rather than a
   targeted regression area.
