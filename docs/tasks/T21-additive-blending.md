# T21 — Extend additive blending on the vector renderer (Phase 2.2)

**Track:** F · **Depends on:** — (independent, can be taken any time) · **Risk:** low (cosmetic, fully revertible) · **Est. diff:** ~30 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Extend the bioluminescent additive-glow aesthetic to the organelles, vesicles and
virus particles **on the existing `PIXI.Graphics` vector renderer** — no sprites,
no image assets, no new dependency.

## Why this task exists separately from Phase 2

`Development_plan.md` Phase 2 has two halves. 2.1 (swap vectors for image sprites)
is **parked** — see `tasks/P01-asset-pipeline-parked.md`. 2.2 (additive blending)
is independent of it and works fine on vector graphics. This task delivers the
2.2 value without touching the parked asset work.

### What is already additive — verify before you start

Established at commit `4bf057f`; confirm it still holds:

| Object | `BLEND_MODES.ADD`? | Where |
|---|---|---|
| `trailGlow` (+ `BlurFilter`, blur 4) | **yes** | layer setup |
| `trailCore` | **yes** | layer setup |
| `golgiGraph` (Golgi cisternae) | **yes** | `drawArcs()` |
| `dynamicLayer` (vesicles) | no | layer setup |
| `organellesLayer` | no | layer setup |
| `virusLayer` | no | layer setup |
| `structGraph` (ER) | no | `drawArcs()` |
| `nucleusLayer`, `mitosisLayer`, `backgroundLayer`, `uiBarsLayer` | no | layer setup |

Also live: a **global `AdvancedBloomFilter`** on `world`
(`threshold: 0.3, bloomScale: 1.5, brightness: 1.2, blur: 8, quality: 4`),
conditional on `PIXI.filters.AdvancedBloomFilter` existing.
`pixi-filters@5.2.1` **is** loaded from CDN alongside `pixi.js@7.3.2`, so that
filter is active — every brightness change you make is amplified by it.

**Read roadmap 2.2 carefully against that table.** Its three literal targets are
"player head cores, active traces, and vesicle drop zones". Player heads and
traces are both drawn into `trailGlow`/`trailCore` (see `drawTraces()`), and the
Golgi *is* the vesicle drop zone. **So 2.2's letter is already satisfied.**

This task is therefore an explicit *extension* beyond 2.2's wording, to the
elements the lost Phase 2 attempt also converted (organelles, vesicles, virus).
State that in the commit message so nobody later thinks 2.2 was previously
missing.

---

## The trap: additive blending kills dark fills

The original rationale for `ADD` was that it makes the **dark backgrounds of JPEG
textures** blend invisibly. Vector graphics have no dark background — they have
alpha. Under `ADD`, the destination is *added to*, so a near-black fill adds
almost nothing and **becomes invisible**.

Several draw calls in this codebase use dark fills deliberately. The one directly
in scope:

```
// updateVesicles(), lysosome-cargo vesicle body
dynamicLayer.beginFill(0x0d0d1a, 0.6);      // near-black — vanishes under ADD
dynamicLayer.lineStyle(2, 0xff4757, 0.6);
dynamicLayer.drawCircle(v.x, v.y, v.radius);
```

Setting `dynamicLayer.blendMode = ADD` will erase that dark body and leave only
the red ring and the two white highlight dots. That may look fine, or it may look
broken — **you must look at it**, not reason about it.

Before changing any blend mode, **search the draw routine you are about to convert
for dark fills** (`0x0d0d1a`, `0x000000`, and any colour whose components are all
below ~0x30) and list them in `## Dark fills` at the bottom of this file. For each
one, decide: brighten it, drop it, or exclude that element from the conversion.

Out of scope but worth knowing: `mitosisLayer` (bridge floor,
`beginFill(0x0d0d1a)`) and `backgroundLayer` (`cellBg`) both rely on dark fills
for the arena silhouette. **Do not make those layers additive** — the arena would
lose its boundary entirely.

---

## The second trap: `blendMode` does not inherit

`organellesLayer` is declared as a `PIXI.Graphics` but is used as a **container** —
organelle sprites are added to it via `organellesLayer.addChild(sprite)` in
`generateMap()` and re-parented in `drawMitosisVisuals()`.

In PixiJS, `blendMode` is a **per-display-object** property. It is not inherited
by children. So:

```
organellesLayer.blendMode = PIXI.BLEND_MODES.ADD;   // does NOTHING to the organelles
```

That line would only affect geometry drawn *directly into* `organellesLayer` —
and nothing is. Set the blend mode on **each organelle `Graphics`**, inside
`createOrganelleGraphics()`, right where the sprite is created. That is one line
in one place and it covers every organelle for free, including ones created later.

`dynamicLayer` and `virusLayer` **are** drawn into directly, so layer-level
assignment works for those two.

---

## Implementation plan

Do these one at a time, looking at the result after each. Stop and keep whichever
subset actually looks better — a partial conversion is a perfectly good outcome.

### Step 1 — Organelles

In `createOrganelleGraphics()`, set `sprite.blendMode = PIXI.BLEND_MODES.ADD;` on
the returned `Graphics`.

Check both branches of that function (mitochondria and lysosome) for dark fills
first. Watch for: overlapping organelles now brightening each other, and
organelles over a player trail blowing out to white.

### Step 2 — Vesicles

`dynamicLayer.blendMode = PIXI.BLEND_MODES.ADD;` at the layer declaration.

Then handle the lysosome-cargo dark body identified above. Recommended: replace
`0x0d0d1a` with a dim version of the cargo colour rather than deleting the fill,
so the vesicle keeps a body instead of becoming a hollow ring.

### Step 3 — Virus particles

`virusLayer.blendMode = PIXI.BLEND_MODES.ADD;` at the layer declaration.

The virus is drawn in bright orange/red (`0xe67e22`, `0xff4757`, `0xffa502`) with
no dark fills, so this is the safest of the three. During the swarm there can be
many particles overlapping — check the brightest case (Step 5).

### Step 4 — ER (optional)

`structGraph` in `drawArcs()` is the ER. It is a lethal wall, so its **readability
matters for fairness**, not just looks. Only make it additive if it stays at least
as legible against the background. If in any doubt, leave it — and say so in the
commit message.

### Step 5 — The whiteout check

Additive brightness stacks, and the global bloom (`threshold: 0.3`) amplifies
anything above its threshold. Construct the brightest possible frame and look at
it:

- 4 players (`currentMode = 4`) with long traces
- vesicles at the cap (25)
- an active virus swarm
- overlapping organelles
- all of the above on top of each other near the cell centre

The fuzzer (T04, if landed) reaches this state on its own; otherwise force it
manually. If anything washes out to unreadable white, **reduce alpha on the
elements you converted** rather than reverting the blend mode — the existing draw
calls already pass explicit alphas (`0.6`, `0.8`, `0.85`, `0.9`) that you can
lower.

Do **not** retune the global bloom filter to compensate. That changes the look of
everything including the already-shipped trail glow, and it is out of scope.

### Step 6 — Make it revertible

Put the three blend-mode assignments behind one named constant so the whole
aesthetic can be toggled in one edit:

```
const GLOW_BLEND = PIXI.BLEND_MODES.ADD;   // set to NORMAL to disable the
                                           // bioluminescent look wholesale
```

This is cosmetic work with subjective acceptance criteria — a one-line revert is
worth the constant.

---

## Interactions with other tasks

- **T13 (organelle necrosis)** greys frozen organelles via `sprite.tint`. Tint
  under `ADD` behaves differently from tint under `NORMAL` — a grey tint on an
  additive sprite reduces its contribution rather than making it look like stone.
  T13 already flags this and offers a sprite-rebuild fallback. If T13 has already
  landed, **re-check the necrotic organelles look right** after Step 1 and note
  the result. If T13 has not landed, add a line to `docs/BACKLOG.md` pointing at
  this interaction.
- **T17 (particles)** plans `blendMode = ADD` on its particle layer, consistent
  with this task. No conflict.
- **T18 (warning filter)** adds a full-screen filter on top. Brighter content
  means its effect reads differently — verify the warning window still looks
  distinct after this task, if T18 has landed.
- **P01 (parked asset pipeline)** — nothing here blocks or presumes a future
  sprite swap. These are per-object blend modes that a sprite would inherit
  identically.

---

## Files touched

`260703_Cellsnake.html` only: `GLOW_BLEND` constant + layer declarations
(`dynamicLayer`, `virusLayer`), `createOrganelleGraphics()`, the lysosome-vesicle
dark fill in `updateVesicles()`, optionally `structGraph` in `drawArcs()`.

**No gameplay, physics, or hitbox changes whatsoever.** If your diff touches
`checkCollision`, `raycast`, `rebuildSpatialGrid`, or any hitbox geometry, you
have gone wrong — revert and re-read.

---

## Verification

This task's acceptance is visual, so evidence means screenshots.

1. Console clean.
2. **Before/after screenshots**, same scene, committed or attached to the commit
   message: (a) a quiet round with organelles and vesicles, (b) the brightest
   frame from Step 5, (c) a mitosis event, (d) the infection warning window.
3. **Nothing became invisible.** Every element that was visible before is still
   visible: lysosome-cargo vesicles have a body, organelles read as distinct
   shapes, the arena boundary and bridge floor are unchanged.
4. **No whiteout** in the Step 5 brightest frame. Individual elements remain
   distinguishable.
5. **Readability of lethal things.** Organelles, the ER and the virus are all
   lethal. Each must be at least as easy to see as before — this is a fairness
   check, not an aesthetic one. Verify at all three zoom levels the camera
   produces (mitosis reveal ≈ 0.1, normal play, close play ≈ 1.2).
6. **Zero physics change.** Play a round and confirm collisions occur in exactly
   the same places. Run the regression sweep from `AGENT_CONDUCT.md` §7.6.
7. **Split-screen** renders correctly — the `RenderTexture` path composites
   additive content, which is the most likely place for a surprise.
8. **No performance change.** Blend modes can break Pixi's batching. Measure mean
   frame time with 4 players + max vesicles + virus swarm, before and after.
   Record both numbers. A meaningful regression means the layers stopped
   batching — if so, report it and consider converting fewer objects.
9. **`GLOW_BLEND = NORMAL` restores the previous look** exactly (except for the
   dark-fill colour changes from Step 2, which are permanent — note that).

## Definition of done

- [x] `## Dark fills` filled in below before any blend mode was changed
- [x] Organelle blend set per-sprite in `createOrganelleGraphics()`, not on the layer
- [x] `dynamicLayer` and `virusLayer` converted; dark vesicle body handled
- [x] ER decision made and justified (left NORMAL)
- [x] Brightest-frame check passed with no whiteout
- [x] Before/after screenshots for four scenes
- [x] Frame-time before/after recorded (463.7ms → 447.0ms mean, no regression)
- [x] All conversions behind the `GLOW_BLEND` constant
- [x] Zero changes to physics, hitboxes, or gameplay
- [x] `docs/TASKS.md`: T21 → `DONE`

## Rollback

Cosmetic and subjective. If the result is not clearly better than the vector look
it replaces, **revert it** — that is a legitimate outcome, not a failure. Record
what you saw and why you reverted under `## Blocked`, with the screenshots. That
finding is worth as much as a merge, and it is directly relevant to whether P01
is ever worth restarting.

---

## Dark fills

Found by reading `createOrganelleGraphics()` and the `updateVesicles()` lysosome
branch before changing any blend mode, at commit `f4d276f`:

| Location | Call | Decision |
|---|---|---|
| `createOrganelleGraphics()`, lysosome branch, body fill | `sprite.beginFill(0x0d0d1a, 0.6)` | Replaced with a dim red (`lysoDarkBody`: `0x330e11` normal / `0x161616` necrotic) at the same alpha, so ADD still gives the body colour instead of erasing it. Same pattern as the vesicle instance the task quotes. |
| `updateVesicles()`, lysosome-cargo vesicle body fill | `dynamicLayer.beginFill(0x0d0d1a, 0.6)` | Same fix: `0x330e11` (dim red) at alpha 0.6. Confirmed with a close-up screenshot (`lyso_vesicle_closeup.png`) — the vesicles keep a visible body, not a hollow ring. |
| `createOrganelleGraphics()`, mitochondria branch, two separator strokes | `drawPill(w - 6, 0x0d0d1a, 1.0)` and `drawPill(w - 14, 0x0d0d1a, 1.0)` | Not quoted in the task but found by reading the whole function per §3 of AGENT_CONDUCT.md. These carved a dark groove between the outer ring and the core under NORMAL blending. Under ADD, `src(≈0)*alpha` contributes nothing regardless of alpha, so the groove silently vanished and the three remaining colour strokes stacked additively into a whiteout (confirmed by screenshot — a solid white blob, cristae detail gone). **Dropped** both separator strokes (dead draws under ADD) and **lowered** the three surviving alphas (0.2→0.15, 0.6→0.32, 0.8→0.55) so the pill reads as a graded green-to-mint glow instead of blowing out. The double-outline "groove" detail is permanently lost — this is the accepted, unavoidable cost of ADD (it can only brighten, never darken a groove) — but the pill stays clearly legible and distinct from the round lysosome shape at every zoom level checked. |
| `structGraph` (ER), `drawArcs()` | `RIBO_COLOR` circles, no near-black fills found | Not converted (Step 4 left optional). The ER is a lethal wall and fairness-critical; converting it was not needed to satisfy 2.2's letter or this task's extension scope, so it was left at NORMAL rather than risk legibility for a hazard nobody asked to change. |
| `mitosisLayer` bridge floor, `backgroundLayer` (`cellBg`) | `beginFill(0x0d0d1a)` | Out of scope per the task file itself — left untouched, not made additive. |

T13 interaction: necrotic organelles are rebuilt via `createOrganelleGraphics(pick, true)`
(a full sprite rebuild with grey colours, not a `.tint` multiply — T13 already
avoided the tint trap), so there was no additional tint-under-ADD issue. Verified
with `window.setGeneration(2)` and a screenshot (`necrosis.png`): the necrotic
organelle reads as a distinct grey/white shape against the healthy green ones.
