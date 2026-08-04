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

- [ ] `## Findings` lists the effects that existed when this was implemented
- [ ] Three tiers, applied through one `applyQuality()` function
- [ ] Effects disabled with `filters = null`, verified
- [ ] Auto-detection with wide hysteresis, at most one change per round
- [ ] Manual override disables auto for the session
- [ ] Frame-time LOW vs HIGH reported
- [ ] Gameplay provably unaffected by tier
- [ ] `docs/TASKS.md`: T26 → `DONE`; T27 → `READY`

---

## Findings

*(Which expensive effects exist at the time of implementation, and their cost.)*
