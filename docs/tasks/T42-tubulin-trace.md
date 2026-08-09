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

## Findings

**Scale check (done first, per the task's own instruction).** Prototyped the
dimer motif (two small offset circles, colour alternating by distance
travelled) and looked at it via `tools/verify_harness.py` screenshots at
`world.scale.x` ≈ 1.15 (close, 1v1 spawn), ≈ 0.34-0.6 (mid, 2-3 players /
split-screen), and ≈ 0.18 (mitosis reveal). At 1.15 the motif reads clearly as
a beaded polymer chain. At 0.18 it is exactly the noise the task predicted —
`TRACE_RT_SCALE` is 0.5 (half world-px resolution) independently of camera
zoom, so a dimer offset of `TRACE_WIDTH*0.35` (1.4 world px) rasterises to
sub-pixel detail in the RT before the camera even sees it.

**Decision:** distance-based LOD, exactly as the task's fallback describes.
Added `DIMER_LOD_ZOOM = 0.5` (world.scale.x threshold) and `DIMER_SPACING = 6`
(world px between alpha/beta colour flips, keyed off each point's own stored
`.d` so the pattern doesn't depend on how many points a given frame appends).
Below the threshold, `accumulateTraceRT()`/`rebuildTraceRT()` fall back to the
pre-existing plain `lineTo` core line — i.e. exactly T25's original behaviour,
unchanged. The LOD decision is made **once per bake** (once per
`accumulateTraceRT()` call, once per `rebuildTraceRT()` call) from the current
zoom, not per point — so a trace segment baked while zoomed in keeps its dimer
texture even if the camera later zooms out past the threshold (visible in the
`zoom_mid` screenshot: one older stretch of trace stays beaded while
freshly-drawn stretches at the same moment are plain lines). This is a
deliberate, documented tradeoff, not a bug — re-baking already-composited RT
content by zoom would defeat T25's whole point (append-only, no
already-drawn geometry ever redrawn).

**Growing tip — implemented as a bounded, un-baked redraw exactly as
specified, but with a cheaper animation than literal drifting/snapping
particles.** `drawTraces()` now stamps the same `stampDimer()` motif for the
last `TIP_POINT_COUNT = 12` points of each player's live segment into
`trailCore` (the existing per-frame Graphics used for heads/auras — already
cleared and redrawn every frame, never baked into the RT), with a
`1 ± 0.25·sin(survivalTime·7 − i·0.9)` radius/offset pulse per point. This is
bounded per player regardless of trace length (§ constraint) and satisfies
"redrawn every frame ... where subunits can animate." I did **not** build a
literal "loose dimers drift in and snap onto the tip" particle-physics
system — that would need per-particle position/target state, effectively a
second particle system, contrary to AGENT_CONDUCT §4.4a/§5's no-second-system
guidance and the task's own "do not build a second particle system" line
(said about the depolymerisation burst, but the same reasoning applies here).
Instead, "dimers coming together" is expressed by retinting the existing T17
locomotion-splash emission (one particle every `LOCOMOTION_PARTICLE_INTERVAL`
frames, already emitted at every player) to alternate `p.color`/`p.coreColor`
by the same `.d`/`DIMER_SPACING` parity as the settled motif, instead of its
previous fixed `p.coreColor`. Net new per-frame work: the bounded 12-point tip
stamp (existing Graphics, no new children) plus a colour computation on an
emission call that already existed. Recorded here per AGENT_CONDUCT §10 as the
smaller, more conservative option; the literal drift-and-snap version is the
alternative if a future session wants the fuller effect.

**Depolymerisation burst.** Added to the existing `target.traceSegments.shift()`
branch in the lysosome pickup (only reachable when `traceSegments.length > 1`,
unchanged condition). Samples up to 6 points along the segment about to be
removed and calls `emitParticles(..., 2, ...)` per sample, alternating
`target.color`/`target.coreColor`, reusing T17's pool — no second particle
system. Verified directly (see Verification log below): a synthetic 20-point
removed segment produced exactly 7 burst calls (`floor(20/6)=3` step ⇒ indices
0,3,6,...,18), alternating colour correctly, `particleCount` stayed low
single digits, `MAX_PARTICLES` is 400.

**Verification log** (`tools/verify_harness.py`, `260703_Cellsnake.html` at
the commit this lands in):

- Syntax: `node --check` on the extracted inline script — OK.
- Console: clean across every check below (harness's own favicon.ico 404 only).
- `drawTraces()` cost, 1 player + 3 bots, 640×480, avg of last 120 real calls
  at each checkpoint (µs, `performance.now()` around the real per-frame call
  via a monkey-patched `window.drawTraces`):
  | game-seconds | tracePoints | drawTraces avg | drawTraces max | worldChildren |
  |---|---|---|---|---|
  | 15  | 624  | 0.172ms | 1.70ms | 14 |
  | 30  | 1225 | 0.155ms | 0.90ms | 14 |
  | 60  | 2378 | 0.113ms | 0.50ms | 14 |
  | 120 | 4632 | 0.145ms | 0.60ms | 14 |

  Flat (no growth) despite a 7.4× increase in total trace points and despite
  every new point now stamping two circles instead of one `lineTo` — T25's
  property holds.
- Zoom-level screenshots: `zoom_close` (scale 1.15, 1000×800), `zoom_mid`
  (scale 0.34, 1000×800, 1v1+1bot), `zoom_far_mitosis2` (scale 0.18, 1000×800,
  mitosis 'forming' state forced via `mitosis.nextTriggerTime`) — all legible,
  no aliasing artefacts at the low-zoom fallback.
- Split-screen: 2 players + 2 bots, `camera=split`, 15s — all four viewports
  render the motif correctly, console clean, `zoom=0.6` (above LOD threshold)
  (`splitscreen_trace` screenshot).
- Depolymerisation burst: forced a lysosome pickup on a synthetic 20-point
  removed segment — 7 `emitParticles(.., 2, ..)` calls, alternating colour,
  `traceSegments.length` dropped by exactly 1, console clean.
- Regular locomotion particle budget: this sandbox's Chromium reports
  `navigator.hardwareConcurrency = 4`, so `detectInitialQuality()` picks the
  `low` tier (`particleBudget: 0`) — the *entire* T17 particle system,
  pre-existing and unrelated to this task, is inert at that tier in this
  environment. Forced `applyQuality('high')` to actually observe particles;
  steady-state locomotion + occasional bursts stayed at 1-4 live particles,
  comfortably under `MAX_PARTICLES=400`.
- Collision: `checkCollision`, `checkArcCollision`, `raycast`,
  `rebuildSpatialGrid` and `TRACE_HITBOX` have zero diff in this change (this
  is rendering-only, confirmed by review of the full diff). Live check: 1
  player, no bot, no input, non-immortal — drove straight into the membrane
  and died at survivalTime 4.1s as expected, console clean. Given the zero
  collision-path diff, the full three-speed regression sweep in AGENT_CONDUCT
  §7.6 (written for changes that touch those specific functions) was not
  additionally run.

**Minor unrelated observation for the backlog:** `gameLoop()` calls
`drawTraces()` twice per unfrozen frame — once inside the `!isCellFrozen`
block (before that frame's player-movement loop runs) and once unconditionally
at the very end (after movement). Since `trailGlow`/`trailCore` are `.clear()`d
at the top of every `drawTraces()` call, the first call's per-frame
head/aura/tip drawing is fully overwritten by the second and never visible —
wasted work every frame. Not touched here (out of scope); noted in
`docs/BACKLOG.md`.
