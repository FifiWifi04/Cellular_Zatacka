# T42 — Render the trace as a microtubule of tubulin dimers

**Track:** K · **Depends on:** T33 · **Risk:** high (touches the hottest render path) · **Est. diff:** large

Read `docs/AGENT_CONDUCT.md`. **Do not start this before T33** — it rewrites the
same trace rendering path whose bounds bug T33 fixes.

## The idea

> "Would it be possible to make the trace tiny microtubules based on tubulin
> dimers, and have an animation of small tubulins coming together when the trace
> is forming, and tubulins dissociating when eating red vesicles?"

Biologically apt and thematically perfect: microtubules *are* polymers of tubulin
dimers that grow by adding subunits at the tip and shrink by catastrophic
depolymerisation. The game already uses "microtubule" for the mitosis scaffolding
(`mitosis.microtubules`) — pick a wording in the UI that keeps the two distinct.

## The constraint that shapes everything

T25 made trace rendering **append-only into a persistent RenderTexture**, which is
why per-frame cost is flat instead of growing linearly. That property must
survive.

So split the visual into two parts:

- **The settled polymer** — everything behind the head. Still drawn **once**,
  accumulated into the trace RT exactly as now. Instead of a plain line segment,
  each appended step stamps a short **dimer motif** (two small offset circles,
  alternating colour for α/β tubulin, rotated to the direction of travel). Cost
  per frame stays proportional to *new* points only.
- **The growing tip** — the last ~10–20 points near the head, redrawn every frame
  in a normal `Graphics` on top, where subunits can animate: a few loose dimers
  drifting in and snapping onto the tip. This is bounded work, independent of
  trace length.

**Never animate the settled polymer.** The moment anything behind the head has to
be redrawn per frame, T25's win is gone and the game degrades over the round
again.

## Depolymerisation on red-vesicle pickup

The lysosome/red pickup already removes trace from the front
(`traceSegments.shift()`), which forces a full RT redraw. Use that moment: emit a
burst of loose dimer particles from the removed region via T17's existing pooled
emitter — **do not** build a second particle system.

## Scale check — do this first

`TRACE_WIDTH` is 4 px, and the camera zooms from 0.1 to 1.2. At the mitosis
reveal (~0.1) a dimer motif is sub-pixel and will alias into noise. **Before
implementing, prototype the motif and look at it at all three zoom levels.** If it
only reads at close zoom, fall back to a distance-based level of detail: dimers
close in, plain line far out. Record the decision in `## Findings`.

## Verification

1. Console clean.
2. **Per-frame `drawTraces()` cost still flat** — the T25 measurement repeated at
   15/30/60/120 game-seconds. This is the test that matters most; if cost grows
   with trace length, the design has been broken.
3. Legible at all three zoom levels; screenshots of each.
4. Growing-tip animation visible and smooth.
5. Depolymerisation burst fires on red pickup, using T17's pool — peak
   `particleCount` still under `MAX_PARTICLES`.
6. **Collision completely unchanged** — this is rendering only. `TRACE_HITBOX`,
   `rebuildSpatialGrid` and `checkCollision` untouched.
7. `worldChildren` flat; RT memory unchanged.
8. Split-screen and mitosis (post-T33 bounds) both correct.
9. Regression sweep §7.6.
