# T18 — Warning-window post-processing filter

**Track:** D · **Depends on:** T16 · **Risk:** medium (GPU cost) · **Est. diff:** ~50 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Apply a full-screen post-processing effect **only** during the one-minute
`infection.state === 'warning'` window.

Roadmap 4.3:

> Apply full-screen post-processing filters (e.g. slight chromatic aberration or
> blur) exclusively during the 1-minute `infection.state === 'warning'` window.

---

## Prerequisites

Read: the `infection` state object, `updateInfection()` (find where `state`
becomes and stops being `'warning'`, and confirm the window's actual duration),
the existing filter usage at init (`PIXI.BlurFilter` on `trailGlow`, and the
`AdvancedBloomFilter` block), and `isCellFrozen` in `gameLoop`, which already
special-cases the warning window.

**Already established — `pixi-filters@5.2.1` is loaded** from CDN alongside
`pixi.js@7.3.2`, so the whole `PIXI.filters` set is available, and the global
`AdvancedBloomFilter` on `world` is active (its `if (typeof
PIXI.filters.AdvancedBloomFilter !== 'undefined')` guard passes). You therefore
have more than the built-ins to choose from.

**Still establish and write under `## Findings`:** which specific filter classes
you used, and — importantly — how your filter interacts with the **existing
global bloom**, which is applied to `world` and will compose with anything you
add. **Do not add a new CDN dependency** and do not retune the global bloom — see
`AGENT_CONDUCT.md` §2.

---

## Design

### Choose the effect from what is actually available

Ranked by cost and by "does it exist without a new dependency":

1. **`ColorMatrixFilter`** — always built in. Desaturate + push toward sickly
   green/yellow, plus a contrast bump. Very cheap. This alone reads strongly as
   "something is wrong" and is the recommended primary.
2. **`NoiseFilter`** — built in, very cheap. A little grain on top of (1) sells
   the biological-distress mood.
3. **`BlurFilter`** — built in, but full-screen blur is the most expensive option
   here. If used, keep the strength very low (1–2) and measure.
4. **Chromatic aberration / RGB split** — available from `pixi-filters@5.2.1`,
   which **is** loaded (`RGBSplitFilter`, `GlitchFilter`). Genuinely available, but
   more expensive than (1)+(2) and easy to overdo. Try only after (1)+(2) are
   working, and keep the offset to 1–2px.

Start with `ColorMatrixFilter` + `NoiseFilter`, both built in. Ship that, then
consider `RGBSplitFilter` as an increment if it still reads too subtle.

### Where to apply it

Apply to the **stage or `shakeRoot`**, not to `world`, and not to individual
layers.

- Applying to `world` means the split-screen `RenderTexture` path renders `world`
  *with* the filter into each viewport, then the composite is drawn — you get the
  effect applied per-viewport, which may double up. Read the split-screen block
  and decide.
- Applying to `shakeRoot` (from T16) or `app.stage` filters the final composite
  once. **Prefer this.**

Confirm your choice by actually testing in split-screen mode.

### Lifecycle — this is where it leaks

**Create the filter instances exactly once at init.** Never in `gameLoop`.

Toggle by assigning and clearing the filter array:

```
// on entering the warning window
target.filters = [colorMatrixFilter, noiseFilter];
// on leaving
target.filters = null;
```

`filters = null` (not `[]`) is what lets Pixi skip the whole filter pass and its
render-texture allocation. Verify by checking frame time outside the window is
unchanged from before the task.

Drive the toggle off a **state transition**, not a per-frame assignment:

```
if (infection.state === 'warning' && !filterActive) { ...enable...; filterActive = true; }
else if (infection.state !== 'warning' && filterActive) { ...disable...; filterActive = false; }
```

Reassigning `filters` every frame allocates and is a real cost.

### Ramp

A hard on/off snap will look cheap. Ramp the effect strength in over ~0.5s and out
over ~0.5s by animating the `ColorMatrixFilter`'s blend amount and the
`NoiseFilter`'s `noise` value. Keep the filter **attached** for the whole ramp and
detach only when the ramp-out completes.

### Reset

`startRound()` must force `filters = null` and `filterActive = false`. A round
that ends mid-warning must not leave the next round filtered.

---

## Files touched

`260703_Cellsnake.html` only: filter instances at init, toggle + ramp block in
`gameLoop`, `startRound()` reset.

---

## Verification

1. Console clean — **including no WebGL warnings**, which are the usual sign a
   filter is misconfigured.
2. **Fires only in the warning window.** Fast-forward (`Tab`/`]`) to the infection
   warning. The effect appears when `infection.state === 'warning'` and is
   completely gone the moment it changes. Verify with a console log of the state
   alongside a visual check.
3. **Nothing outside the window.** Play 3 minutes of normal play; the frame must
   be visually identical to pre-task. Compare screenshots.
4. **Frame time outside the window unchanged.** Measure mean frame time before
   and after the task during normal play. Any regression means `filters` is not
   actually `null`.
5. **Frame time inside the window acceptable.** Measure during the warning.
   Record both numbers. If the drop is severe, downgrade to `ColorMatrixFilter`
   alone.
6. **Split-screen.** Trigger the warning in split-screen mode. The effect must
   apply once to the composite and both viewports must render correctly.
7. **Ramp is smooth**, no popping at either end.
8. **Reset.** Restart the round mid-warning. The new round must be unfiltered.
9. **No leak.** `worldChildren` flat, and heap flat, across 10 warning cycles
   under the fuzzer — filters are a classic source of retained render textures.

## Definition of done

- [ ] `## Findings` filled in: which filter classes the loaded PixiJS build provides
- [ ] Filters instantiated once at init, never in `gameLoop`
- [ ] Toggled on state transition, `filters = null` when inactive
- [ ] Applied to the composite, verified in split-screen
- [ ] Smooth ramp in/out
- [ ] Reset on `startRound()`
- [ ] Frame time inside and outside the window recorded
- [ ] `docs/TASKS.md`: T18 → `DONE`

---

## Findings

*(Fill in during the task: which `PIXI.filters` are available, and which you used.)*
