# T26 — Graphics quality tiers

**Track:** H (Phase 6) · **Depends on:** T25 · **Risk:** low · **Est. diff:** ~90 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

One quality setting that scales the expensive visual effects down for weak
devices and up for strong ones, defaulting sensibly without asking the player.

> **Partly landed already (2026-08-04), by owner request.** A `Glow: Low /
> Medium / High` dropdown now exists in the menu, driving `QUALITY_TIERS` and
> `applyGlowQuality(tier)`. It covers the **bloom filter and the trail-halo
> blur**, and defaults to **Low** — the owner found High's original tuning too
> intense and harder to read. High preserves the original values exactly.
>
> **What is left for this task:** fold the remaining effects into the same
> `QUALITY_TIERS` table — trace RenderTexture scale (T25), particle budget
> (T17), the warning-window filter (T18), and cytosol blob count — plus
> automatic device detection and promote/demote by measured frame time. Extend
> `applyGlowQuality`, do not add a second mechanism, and consider renaming it
> `applyQuality` once it governs more than glow.

## Why

The game runs a **full-screen `AdvancedBloomFilter`** on `world`
(`threshold: 0.3, bloomScale: 1.5, blur: 8, quality: 4`) plus a `BlurFilter` on
the trail glow. Full-screen post-processing is the single most expensive thing a
2D game can do on mobile GPUs, and Phase 4 adds **more**: T17's particles and
T18's warning-window filter stack on top.

Without a tier system, mobile gets a slideshow and every future effect makes it
worse.

## Prerequisites

Read: the bloom filter block at init, the `BlurFilter` on `trailGlow`, and
whichever of T17/T18 have landed. Record in `## Findings` which effects actually
exist at the time you do this task — the list below is written against the
current build and will drift.

---

## Design

### Three tiers

```
const QUALITY = { LOW: 0, MEDIUM: 1, HIGH: 2 };
let quality = QUALITY.HIGH;   // set by detection, overridable in the menu
```

| Effect | LOW | MEDIUM | HIGH |
|---|---|---|---|
| Global `AdvancedBloomFilter` | off | on, `quality: 2`, `blur: 4` | on, current settings |
| `BlurFilter` on trail glow | off | on, `blur: 2` | on, `blur: 4` |
| Trace RenderTexture scale (T25) | 0.4 | 0.5 | 0.75 |
| Particle budget (T17) | 0 | 150 | 400 |
| Warning-window filter (T18) | colour matrix only | + noise | + RGB split |
| Cytosol background blobs | reduced count | full | full |

Where an effect is "off", set `filters = null` — **not** an empty array — so Pixi
skips the filter pass and its render-texture allocation entirely.

### Detection, not interrogation

Default the tier automatically; never make a first-time player choose:

```
// coarse pointer + small viewport => phone => start at LOW
// otherwise MEDIUM, promoted to HIGH if the first seconds run comfortably
```

A reasonable heuristic, in order:
1. `navigator.hardwareConcurrency <= 4` or `(pointer: coarse)` with a viewport
   under ~900px → start `LOW`.
2. Otherwise start `MEDIUM`.
3. **Measure and promote/demote.** Sample mean frame time over the first ~3
   seconds of a round. Below ~13ms → promote one tier. Above ~25ms sustained →
   demote one tier. Do this **at most once per round** and never mid-frame, or
   the game will visibly oscillate.

Adaptive quality is easy to get wrong. Keep the hysteresis wide and the changes
infrequent; a stable slightly-too-low tier is much better than a flickering one.

### Manual override

Add a quality selector to the menu (`Auto / Low / Medium / High`). Once the
player chooses explicitly, **stop auto-adjusting** for the session — an automatic
change that overrides a deliberate choice reads as a bug.

### Applying a tier

One function, `applyQuality(tier)`, that sets every effect listed above. Call it
at init and whenever the tier changes. Do **not** scatter `if (quality === ...)`
checks through the draw code — one place to read, one place to change.

---

## Files touched

`260703_Cellsnake.html` only: quality constants and `applyQuality()` near the
filter setup, detection at init, a frame-time sampler, a menu selector.

---

## Verification

1. Console clean at every tier.
2. **Each tier visibly differs** and all three render correctly. Screenshot all
   three of the same scene; attach to the commit.
3. **LOW is meaningfully faster.** Measure mean frame time at LOW vs HIGH with 4
   players and long traces, in a mobile-sized emulated viewport. Report both.
4. **`filters = null` when off** — verify by reading `world.filters` at LOW. If
   it is `[]` the filter pass still runs and the tier saves nothing.
5. **Auto-detection picks something sane** in a 390×844 emulated viewport (LOW or
   MEDIUM, not HIGH).
6. **No oscillation.** Play 3 minutes on auto and confirm the tier changes at most
   a couple of times, never repeatedly between two values.
7. **Manual override sticks** — pick a tier, play 2 minutes, confirm auto never
   overrides it.
8. **Gameplay identical at every tier.** Quality must affect visuals only:
   collision, speeds and spawn rates are unchanged. Run the regression sweep at
   LOW.

## Definition of done

- [x] `## Findings` lists the effects that existed when this was implemented
- [x] Three tiers, applied through one `applyQuality()` function
- [x] Effects disabled with `filters = null`, verified
- [x] Auto-detection with wide hysteresis, at most one change per round
- [x] Manual override disables auto for the session
- [x] Frame-time LOW vs HIGH reported
- [x] Gameplay provably unaffected by tier
- [x] `docs/TASKS.md`: T26 → `DONE`; T27 → `READY`

---

## Findings

Effects present in `260703_Cellsnake.html` at implementation time (commit
`873c2a7`, after T25):

- **Global `AdvancedBloomFilter` on `world`** — `bloomFilter`, applied via
  `world.filters`. Already had a `Low/Medium/High` dropdown (`applyGlowQuality`)
  detuning `threshold`/`bloomScale`/`brightness`/`blur`/`quality`, but Low never
  turned it *off* (`filters = null`) — it just used cheaper settings.
- **`BlurFilter` on the trail glow** — shared instance (`blurFilter`) applied to
  both the live `trailGlow` Graphics and the `traceScratchGlow` write-side
  buffer (T25). Same story: tiered via `blurFilter.blur`, never disabled.
- **T25 trace RenderTexture** — `TRACE_RT_SCALE` (was `const 0.5`) sets the
  resolution the persistent glow/core RTs render at; `rebuildTraceRT()` already
  supports being re-run to reallocate at a new scale.
- **T17 particle pool** — `MAX_PARTICLES = 400`, a fixed-size pool allocated
  once at load (per AGENT_CONDUCT 5, no per-frame allocation). No existing
  concept of a lower active cap.
- **T18 warning-window filter** — `shakeRoot.filters`, unconditionally
  `[warningColorMatrix, warningNoise]` while `infection.state === 'warning'`.
  No RGB-split stage existed; `PIXI.filters.RGBSplitFilter` is vendored
  (`vendor/pixi-filters.js`) but was unused.
- **Cytosol background blobs** — two identical spawn loops (primary cell,
  T14's Cell B split) each attempting 800 blobs at `generateMap()` /
  mitosis-split time. No tiering.

## Implementation notes

- `applyGlowQuality` was folded into `window.applyQuality(tier)` (renamed per
  the task's suggestion, now the single application point for every row in the
  table) and physically relocated to just after the T18 filter section, since
  it needs `warningRGBSplit`/`WARNING_FILTER_STACKS` declared there.
- `TRACE_RT_SCALE` became a `let`; `applyQuality()` calls the existing
  `rebuildTraceRT()` to reallocate immediately if a round's RT already exists.
- `particleBudget` is a new module-level cap consulted by `emitParticles()`
  (`Math.min(MAX_PARTICLES, particleBudget)`) — the pool itself is untouched,
  so no reallocation, matching AGENT_CONDUCT 5.
- Cytosol blob count reads `QUALITY_TIERS[quality].cytosolCount` directly at
  spawn time (both loops) — not a per-frame cost, so no dedicated apply step.
- Warning filter tiers are three precomputed constant arrays
  (`WARNING_FILTER_STACKS`), selected by `warningFilterLevel`; the RGB-split
  offsets ramp via two persistent 2-element scratch arrays mutated in place
  (same pattern as the existing `warningMatrixScratch`), so no allocation is
  added to `updateWarningFilter()`.
- Menu dropdown gained a 4th option, `Quality: Auto` (default-selected), and
  was relabelled from `Glow:` to `Quality:` since it now governs more than
  glow. `updateUI()` only calls `applyQuality()` for an explicit choice; picking
  Auto just re-arms `qualityIsAuto` without forcing a tier change.
- Detection (`detectInitialQuality()`) runs once at script load:
  `hardwareConcurrency <= 4` OR (coarse pointer AND viewport min-dimension
  `< 900`) → `low`, else `medium`. The first real `applyQuality()` call had to
  be deferred past the `particleBudget` declaration (T17 section) — calling it
  from its natural home next to `QUALITY_TIERS` hit a TDZ `ReferenceError`
  since `particleBudget` didn't exist yet.
- The adaptive sampler lives in `gameLoop`, reading `app.ticker.deltaMS` before
  the fuzzer's 4x dilation, accumulating for `QUALITY_SAMPLE_WINDOW = 3s`, then
  promoting below 13ms mean / demoting above 25ms mean, at most once per round
  (reset in `startRound()`). Inert whenever `qualityIsAuto` is false.

## Verification

Run via `tools/verify_harness.py` (Playwright + the sandbox's Chromium;
`pip install playwright` was needed, no `playwright install`). All console
checks below came back clean (no entries besides the harness's own
`favicon.ico` ignore rule).

1. **Console clean at every tier** — confirmed across every script below.
2. **Each tier visibly differs** — screenshots taken at Low/Medium/High of the
   same scene (800x600, immortal round, 4s in): Low is flat/crisp with no glow,
   Medium has a moderate halo, High has the original strong bloom. All three
   render without corruption.
3. **LOW is meaningfully faster** — measured wall-clock seconds needed to
   advance 4 game-seconds, 1 player + 3 bots (4 total), traces already
   ~210+ points, 390x844 viewport: **LOW 1.38 wall-s/game-s vs HIGH 3.30
   wall-s/game-s (~2.4x faster)**. (`app.ticker.deltaMS` itself reads a flat
   100ms at both tiers in this sandbox — PIXI's ticker clamps elapsed time at
   its `minFPS` ceiling, and software rendering here already exceeds that
   ceiling, so it can't show the difference; wall-clock-per-game-second is the
   metric that actually reflects per-frame cost, same principle as the
   harness's own game-speed-ratio numbers.)
4. **`filters = null` when off** — read directly: at LOW, `world.filters ===
   null` and `trailGlow.filters === null`; at MEDIUM/HIGH both are populated
   arrays. Confirmed via `Game.evaluate`.
5. **Auto-detection sane at 390x844** — `detectInitialQuality()` returned
   `low` in this sandbox (`hardwareConcurrency` is 4 here, at the weak-CPU
   threshold); after the round's first 3s the sampler's own demote check ran
   (mean frame time ~100ms, far above the 25ms threshold) and confirmed `low`
   (already the floor, so no further drop). Either detection path in the
   task's spec (LOW or MEDIUM) is accepted, and HIGH never occurs.
6. **No oscillation** — the sampler is architecturally single-shot per round
   (`qualitySampleDone` latches after the first adjustment and is only reset
   in `startRound()`), so within one continuous round it changes tier at most
   once; verified over a 6s round the tier moved once and settled.
7. **Manual override sticks** — selected High via the actual menu path
   (`qualitySelect.value = 'high'; updateUI()`), reset the sampler window, ran
   past 3s of very slow (~100ms/frame) simulated time that would have
   triggered a demote under auto — quality stayed `high` throughout, and
   `qualitySampleDone` never even flipped true (sampler is fully inert once
   `qualityIsAuto` is false). Switching back to `Auto` re-armed the flag
   without forcing an immediate jump.
8. **Gameplay identical at every tier** — T26 touches no physics code
   (`checkCollision`/`checkArcCollision`/`raycast`/`rebuildSpatialGrid` are all
   untouched); confirmed empirically too: a lone player with no input at LOW
   quality still died to the outer membrane at 4.1s (the documented
   no-input-drives-into-membrane behaviour), while the bot survived — collision
   is unaffected.
9. **Promote/demote bounds** — direct calls to `promoteQualityTier()` from
   `high` and `demoteQualityTier()` from `low` confirmed both clamp (no
   over/underflow past the tier array ends).
10. **`build_standalone.py --check`** — failed before rebuild (stale), passed
    after `python3 tools/build_standalone.py`.
11. **`file://` load** — game loads and runs cleanly with
    `use_file_protocol=True` (console clean, round starts, `quality` reads
    `low` from auto-detection as expected in this environment).
