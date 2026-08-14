# T62 — Art pass: the cell reads as a diagram, not as a place

**Track:** K · **Depends on:** T60 (reveal framing), T61 (HUD) · **Risk:** medium (broad visual change) · **Est. diff:** ~200 lines

Owner request, 2026-08-11: *"Inspect the visual of the whole project (different
organelles, bridge, edges, bubbling membrane and etc.) … What could be improved
to make it more appealing, immersive and clear?"*

Screenshots under `/tmp/verify/audit/`. Take **one section per session** — this is
a list, not a single change, and a whole-file restyle in one commit cannot be
reviewed or reverted cleanly (§1.2).

---

## What already works — do not "fix" these

State this up front so a session does not undo it: the nucleus/ER/Golgi cluster
(`08-nucleus-er-golgi.png`) is genuinely good — the ribosome studding, the
chromatin scribble, the concentric Golgi stacks read as cell biology at a glance.
The mitochondria with their cristae are readable and distinct. The trace lattice
(T56) works. The palette — deep indigo ground, cyan/violet structures, warm
accents for hazards — is coherent. **This task is about everything around them.**

## 1. Scale collapse — the arena is beautiful up close and empty far away

Compare `08-nucleus-er-golgi.png` (zoom ≈2.0) with `10-gen2-calcification.png`
(zoom ≈0.5, where the game is actually played). At playing distance the ER and
Golgi shrink to thin arcs, the membrane's three layers collapse into one blue
line, the 28 protrusions vanish, and most of the screen is flat near-black with
scattered translucent circles.

**This is the single biggest visual problem: the detail is all at a zoom nobody
plays at.** Options, pick one and screenshot it at 0.5 and 0.6 before committing:

- Thicken and simplify structures as zoom falls (a genuine LOD, the way T47/T56
  already gate the trace motif) so they stay legible rather than shrinking away.
- Add mid-frequency detail to the cytosol — currently only large soft blobs and
  nothing between them — so the empty regions have texture at playing distance.

## 2. The membrane loses its identity at distance

`13-mitosis-bridge.png`: the wall is one thin blue ellipse outline. All of T49's
work — the three-layer ring, the protrusions riding the wall — is invisible there.
The membrane is the thing that kills you most often; it should read as a
*structure*, not a stroke. Give it a low-zoom treatment: thicker, with a soft
inner glow falling into the cytosol so "inside" and "outside" are unmistakable.

## 3. The mitosis bridge is four straight lines

`13-mitosis-bridge.png`: two green and two blue horizontal segments joining the
cells. Nothing else in the game is a straight line. A dividing cell pinches — the
membrane should neck down into an hourglass and the bridge walls should be curves
continuous with each cell's wall, not a separate primitive butted against them.

This is the game's biggest event and its most schematic-looking moment.

## 4. Depth: everything sits on one plane

There is no parallax, no depth cue except alpha. Two cheap, high-value additions:

- **Parallax on the background blobs** — a slow drift at a fraction of camera
  movement instantly reads as depth and costs almost nothing.
- **A vignette or falloff at the cell edge** so the arena feels enclosed rather
  than cropped.

## 5. Hazard colour language is not consistent

Currently: organelles green, necrotic grey-blue, aggregate amber, chasers pink,
debris grey, membrane blue, nucleus violet. A player cannot answer "will this
kill me?" from colour alone. After T50, "red mode breaks dead matter" is a rule
the player learns — the palette should support it: everything **breakable in red
mode** should share a visual family (desaturated, mineral) distinct from
**always-lethal** structures (saturated, alive). Write the rule down in
`## Findings` as a table and apply it.

## 6. Motion and life

The arena is static apart from drift. Cheap additions with strong returns:
a slow breathing pulse on the membrane; the ER/Golgi rotating at slightly
different rates (they share `globalRotation` today, which is why they read as one
rigid disc); occasional vesicle traffic along the Golgi stacks.

## Verification (per section)

1. Console clean.
2. Before/after screenshots **at the zoom the game is played at** (0.5–0.6 shared,
   0.6 split), not just close up. A change that only looks better at 2.0× has not
   addressed the problem.
3. `drawTraces()` and per-frame cost unchanged — measure, because several of
   these are per-frame draws. Any new per-frame `Graphics` allocation is a defect
   (§4.4a, §5).
4. `worldChildren` flat over 5 minutes.
5. Quality tiers respected: the `low` tier must drop the new detail first.
   Screenshot `low` and `high`.
6. **No gameplay change.** Hitboxes, hazard geometry and collision constants
   untouched — confirm with `git diff`.
7. Legibility check: at 0.5 zoom, a screenshot in which a new player could point
   at each lethal thing. If they blend, the change failed.

## Definition of done

- [ ] Sections taken one per session, each with before/after at playing zoom
- [ ] Hazard colour rule written down as a table and applied
- [ ] Per-frame cost and `worldChildren` unchanged
- [ ] Quality tiers respected
- [ ] No collision or hazard constant touched
- [ ] `docs/TASKS.md`: T62 → `DONE` when every section is done

---

## Progress

- [x] Section 1 — scale collapse (cytosol mid-frequency filler)
- [x] Section 2 — membrane low-zoom treatment
- [x] Section 3 — mitosis bridge as a curve, not four straight lines
- [x] Section 4 — depth (parallax, edge falloff)
- [x] Section 5 — hazard colour language table
- [ ] Section 6 — motion and life (breathing pulse, independent ER/Golgi rotation, vesicle traffic)

Commit per section (`T62: <section>`), push, then decide whether there is
budget for the next. Partial `T62:` commits are expected and do **not** mean
the board is stale. Leave T62 `READY` until every section is ticked.

---

## Findings

**Section 1 (scale collapse), landed 2026-08-14.** Chose the task's second
option — "add mid-frequency detail to the cytosol" — over a genuine
zoom-scaled LOD on the ER/Golgi/membrane line widths, because those are baked
once in `drawArcs()`/`generateMap()` rather than redrawn per frame (unlike the
T42/T47 trace-dimer LOD this section's other option points to), so a real LOD
there means a re-bake-on-zoom-change system — bigger than a first section
should be, and it would also cut into section 2's explicit "give the membrane
a low-zoom treatment" scope. The membrane/ER/Golgi zoom-collapse problem itself
is left for sections 2 and (for the Golgi/ER specifically) a future section —
noted here, not fixed here.

Added `spawnCytosolFiller()`, called once from `generateMap()` for the primary
cell and once from the Cell B branch (mitosis), pushing small (r=3-12),
low-alpha (0.06-0.16) blobs into the *same* `cytosolParticles` array the
existing large blobs use — so the existing per-frame drift/pulse loop in
`drawCalcification()` animates them for free, no new per-frame code. Count is
tier-driven (`QUALITY_TIERS[tier].cytosolFillerCount`: low 0, medium 400, high
600), added as a new field on the existing tier objects rather than a parallel
table, and only spawned on top of the existing `cytosolCount` roll — low tier
gets exactly 0 extra (confirmed: `cytosolParticles.length` 227 at low with
`cytosolFillerCount:0` vs 933/1111 at medium/high with 400/600 filler
requested, matching the ~78-83% ellipse-inscribed-in-square accept rate the
existing large-blob loop already has).

Cost measured by replaying the exact `drawCalcification()` cytosol-forEach
body 200x in-page via `performance.now()`: 0.075ms/frame at 636 particles
(filler forced to 0, i.e. old behaviour) vs 0.109ms/frame at 1095 particles
(filler on) — a 0.034ms increase, negligible against a 16.6ms frame budget.
`worldChildren` flat at 16 across a 300-game-second (5-minute) headless
immortal run (`window.stepHeadless`, dt=1/30, 32.4 wall-seconds). Console
clean across: a quality-tier sweep (low/medium/high, 4 rounds), a real 15s
round (1 human + 3 bots, non-immortal — human died into the membrane as
expected with no input, all 3 bots survived), and an offline `file://` load of
the rebuilt `dist/Cellular_Zatacka.html` (8.2 game-seconds, immortal).
Before/after screenshots taken at zoom 0.55 (forcing `world.scale.set(0.55)`
after round start) by toggling `QUALITY_TIERS.high.cytosolFillerCount` between
0 and 600 across two otherwise-identical high-tier rounds (screenshots not
committed — text findings only, per repo convention). The low-tier screenshot
at the same zoom matches the "before" screenshot's sparseness, confirming the
tier gate. No hazard function appears in the diff
(`checkCollision`/`checkArcCollision`/`raycast`/`rebuildSpatialGrid` all
absent, confirmed by `git diff` grep), so §7.6's regression sweep doesn't
apply. `sw.js` `CACHE_NAME` bumped v41→v42; `dist/` rebuilt (`--check` passes).

**Section 2 (membrane low-zoom treatment), landed 2026-08-14.** `drawCalcification()`
(the sole per-frame membrane draw for `activeCell`, per its own T37 comment)
now computes `zoomBoost = Math.max(1, 1 / world.scale.x)` -- the same
zoom-legibility pattern T52 already uses for the nucleus well in
`drawVesicles()` -- and multiplies every stroke width by it, so the ring no
longer thins out as the camera zooms below 1.0 (the ~0.5-0.6 zoom the game is
actually played at, per section 1's own framing). The three existing rings
were also thickened at their base width (15/8/3 -> 18/10/4 world px) for a
stronger boundary at any zoom. A new soft inner glow -- up to 3 concentric
rings stepping inward from the membrane with decreasing alpha (`0.045 * i`),
same blue family as the existing outer glow ring -- gives "inside" a falloff
into the cytosol instead of ending at a stroke. Glow step count is tier-driven
(`QUALITY_TIERS[tier].membraneGlowSteps`: low 0, medium 2, high 3), the same
gating idiom section 1 established for `cytosolFillerCount`, so low tier drops
the new glow layer entirely (confirmed by screenshot: low-tier membrane keeps
the boosted three-ring stroke but no glow falloff). `zoomBoost` itself is not
tier-gated, matching T52's precedent -- it only changes stroke width on the
existing draw calls, not the calls made, so it adds no cost to gate.

Screenshotted before/after at the true playing zoom (0.55, camera frozen via
a stubbed `updateCamera()` and panned to the membrane edge, since the default
camera keeps the boundary off-screen near round start): before, the ring read
as one thin ~15px line; after, it reads as a thick glowing wall with a visible
falloff into the cytosol, at both high tier (glow present) and low tier (glow
absent, ring still boosted). Also checked at the Gen 2+ calcification floor
(`radiusX`/`radiusY` forced to `CALCIFY_FLOOR`=0.45 of base) -- glow rings stay
valid (innermost ring is `radius - 76` at 3 steps, well clear of the ER/Golgi
cluster) with no clipping or artifacts.

Cost measured by calling `drawCalcification()` directly 3000x per tier via
`performance.now()` after a 50-call warmup: 0.0044ms/call (low, no glow),
0.0058ms/call (medium), 0.0045ms/call (high) -- all sub-millisecond noise
against the 16.6ms frame budget, no meaningful difference between tiers despite
the extra glow draw calls. `worldChildren` flat at 16 across a 300-game-second
headless immortal run. Console clean across: a real 30.2s round (1 human + 3
bots, non-immortal -- human died into the membrane as expected, all 3 bots
survived, confirming membrane death behaviour is unchanged), and an offline
`file://` load of the rebuilt `dist/Cellular_Zatacka.html` (8.2 game-seconds,
immortal). No hazard function appears in the diff
(`checkCollision`/`checkArcCollision`/`raycast`/`rebuildSpatialGrid` all
absent, confirmed by `git diff` grep) -- `activeCell.radiusX/radiusY` (the
actual collision boundary) are read, never written, by this change -- so
§7.6's regression sweep doesn't apply.

Not touched, noted here rather than fixed: the one-time `cellBBg` bake in the
mitosis-trigger block (a separate, static copy of the same three-ring style
drawn once for Cell B at event start) has the identical zoom-collapse problem
but can't reuse a live `zoomBoost` since it's baked once, not redrawn per
frame -- filed to `docs/BACKLOG.md` as a follow-up, out of scope for this
section. `sw.js` `CACHE_NAME` bumped v42->v43; `dist/` rebuilt (`--check`
passes).

**Section 3 (mitosis bridge as a curve), landed 2026-08-14.** Root-caused the
"four straight lines" look before touching anything: `isOutsideCell()`'s bridge
rectangle (the actual hazard geometry, untouched by this section) spans
cell-*centre* to cell-*centre*, so the true safe boundary near each cell is
`max(ellipseExtent(x), halfW)` -- exactly the ellipse's own curve out to the
point where it narrows to the corridor's half-width, flat from there on. The
old code instead started its straight wall at a fixed `radiusX - 10` offset,
which sits *past* that true crossing point, so between the crossing point and
the old wall start the membrane's own ring (still drawn in full by
`drawCalcification()`, unmodified) reads down to ~100px while the new wall
already needed to be at the full 300px half-width -- a real ~200px vertical
jump at the seam, which is what actually read as "a separate primitive butted
against" the cell, not merely a lack of curvature.

Fixed by computing `edgeOffset = rx * sqrt(max(0, 1 - halfW²/ry²))` (swapped
for the vertical direction) each frame in `drawMitosisVisuals()` and using
`gapStart`/`gapLength` (local to that function, not read anywhere else --
confirmed by grep) based on it, so the corridor's flat sides now begin exactly
where the cell's own ellipse boundary is already at the corridor's half-width
-- zero positional jump, for free, since the membrane ring's own draw call is
untouched. A short `quadraticCurveTo` flare (`NECK_FILLET = 70` world px) at
each end then rounds the remaining ~73° *tangent* kink (ellipse tangent vs.
flat wall) into a genuine curve, retracing a short arc of the membrane's own
already-visible curve in the game's own wall colour (`0x4a69bd`, identical to
the membrane's middle ring) rather than introducing a new shape or colour.
Net effect: the corridor now reads as a proper hourglass neck (wide at each
cell, narrowing smoothly to the fixed corridor width) instead of a rectangle
slapped against two circles -- this falls directly out of the corrected
geometry, no separate "hourglass" special-casing was needed.

Purely cosmetic: `isOutsideCell()` (the bridge's real rectangle test,
cell-centre to cell-centre, `mitosis.currentWidth`-driven) is unmodified, and
neither it nor `checkCollision`/`checkArcCollision`/`raycast`/
`rebuildSpatialGrid` appear in the diff (confirmed by `git diff` grep). The
flare's control geometry is derived entirely from the same `activeCell.radiusX/
radiusY`/`mitosis.currentWidth` the real hazard already uses, so it can only
ever retrace true ellipse-boundary points -- there's no way for the drawn wall
to bulge outside the actual safe region and create an invisible-wall death.

Not tier-gated, same reasoning T62 section 2 used for `zoomBoost`: this
reshapes the vertices of the two existing wall subpaths (2 more
`quadraticCurveTo` calls per wall instead of a second `lineTo`), it doesn't add
a new draw call, layer, or particle count to gate. Measured directly:
`drawMitosisVisuals()` cost 0.0202ms/call before vs. 0.0254ms/call after (3000
calls each, `performance.now()`), a 0.005ms delta, noise against the 16.6ms
frame budget.

Verified: before/after screenshots at the true playing zoom (0.55, camera
stubbed and panned to the bridge midpoint, same technique as sections 1-2) for
a forced horizontal (`direction=0`) event -- before shows the exact jump
described above (thick glowing membrane ring cutting hard to a thin flat line);
after shows a continuous curved neck with no seam. A forced vertical
(`direction=3`) event screenshotted clean too, confirming the mirrored branch.
A direct width sweep (`mitosis.currentWidth` = 600, 300, 60, 5, 0.1, 0, calling
`drawMitosisVisuals()` at each) produced no throw/NaN at any value, including
the `narrowing` state's approach to a fully-closed bridge. `worldChildren` flat
at 16 across a real 300-game-second headless immortal run (`window.
stepHeadless`, dt=1/30, forcing repeat mitosis triggers). A real 15s rendered
round (1 human + 3 bots, non-immortal) played normally, console clean. Offline
`file://` load of the rebuilt `dist/Cellular_Zatacka.html` also console-clean
with a forced mitosis event. `sw.js` `CACHE_NAME` bumped v43->v44; `dist/`
rebuilt (`--check` passes).

One pre-existing, already-backlogged issue surfaced incidentally while
diagnosing an early-terminating headless run: the mitosis snap's "kill players
left behind" check (`updateMitosis()`, "4. Kill players who didn't make it to
Cell B") is gated on `devMode`, not `godMode`, so an uncontrolled human slot in
an `immortal: true` harness run can still die at the snap even though
collision itself is disabled -- this is the same issue T51's Findings already
filed to `docs/BACKLOG.md`; not re-filed, and out of scope here regardless
(it's `updateMitosis()` state logic, not this section's draw-only change).

**Section 4 (depth: parallax + edge falloff), landed 2026-08-14.** Two additions,
both in the two functions section 2/3 already own (`drawCalcification()`,
`updateAndDrawBackgroundElements()`) rather than a new system.

*Parallax.* `cytosolContainer` (the shared container both the large blobs and
T62 section 1's filler blobs live in) gets its own position, recomputed fresh
every frame in `updateAndDrawBackgroundElements()` from the camera's current
focus point (`(app.screen.width/2 - world.x) / world.scale.x`, i.e. the world
point the camera currently centres on -- no new camera state needed) minus
`activeCell.x/y`, scaled by `PARALLAX_STRENGTH = 0.15`. This is recomputed from
that stored base every frame, never accumulated from a delta, so it can't drift
the way AGENT_CONDUCT 4.5 warns `world.x/y` itself could. The blobs' own local
`x`/`y` fields (world coordinates, read by the existing `isOutsideCell()`
pull-back-inside-membrane logic) are untouched -- only the container's
rendering-time offset changes, the same relationship `world.x/y/scale` already
has to every other layer's local coordinates. Verified algebraically and in
the browser: forcing `world.x/y/scale` to a known camera position and reading
`cytosolContainer.x/y` back matched the formula's prediction to floating-point
precision (`containerX: 74.99999999999996` against `expectedX: 75` for a
camera focus 500/300 world px off the cell centre). Not tier-gated -- same
precedent as section 2's `zoomBoost` (T52's), since it's two divisions/two
multiplications per frame regardless of particle count, not a new draw call to
gate.

*Edge falloff.* A first attempt drew outward rings in a near-black tone
(`0x05050d`) stepping out from the membrane, meant to read as a vignette --
screenshotted at the true playing zoom (0.55, camera stubbed and panned to the
membrane's rim, same technique sections 2-3 used) and found genuinely
indistinguishable from the flat `backgroundColor` (`0x0a0a14`): the two tones
are close enough that no alpha low enough to stay "subtle" was visible at all.
Replaced with rings in the membrane's own outer-glow blue (`0x1e3799`, the
same colour section 2's *inward* glow already uses) bleeding *outward* with
decreasing alpha (`0.14 / i` over `glowSteps` rings, stroke width `40 *
zoomBoost`, spaced `40` world px apart) -- same `glowSteps`
(`QUALITY_TIERS[tier].membraneGlowSteps`)/`zoomBoost` the inward loop already
uses, so low tier drops it entirely and it stays legible at any zoom. Before/
after screenshots at the membrane rim (0.55 zoom, camera frozen via a stubbed
`updateCamera()`) confirm the difference: before, the wall cuts straight to
flat near-black outside the ring; after, a soft blue halo bleeds visibly
outward before fading to nothing, at high tier -- and the low-tier screenshot
at the same camera position matches the "before" shot almost exactly (hard
edge, no halo), confirming the tier gate actually drops the added detail
first, not just in principle.

Cost measured directly (`drawCalcification()`/`updateAndDrawBackgroundElements()`
called 3000x via `performance.now()`, quality pinned to `high` in both the
pre-section-4 baseline via `git stash` and the final code, same technique
prior sections used): `drawCalcification()` 0.0099ms/call before vs.
0.0111ms/call after (both noise against the 16.6ms frame budget);
`updateAndDrawBackgroundElements()` 0.1365ms/call before vs. 0.1231ms/call
after (no measurable increase -- the difference is within this sandbox's own
software-rendering timing noise, confirmed by the before run actually having
*more* live particles (238 vs 236) yet a similar-or-higher time). `calcifyLayer`
draw-call count confirmed via a tier sweep: low 3 (unchanged, both new loops
gated off), medium 7, high 9 (3 base rings + 3 inward + 3 outward, matching
`glowSteps`). `worldChildren` flat at 16 across a real 300-game-second headless
immortal run (`window.stepHeadless`, dt=1/30, 33.6 wall-seconds -- consistent
with the ~17.5x headless speedup T22 step 7 measured). A real 13.9s round (1
human + 3 bots, non-immortal) played and ended normally on its own (bots
fighting down to one survivor, the standard last-one-standing end condition --
unrelated to this change), console clean, round-over card rendered correctly.
An offline `file://` load of the rebuilt `dist/Cellular_Zatacka.html` (8.2
headless game-seconds, immortal) also console-clean. `git diff` confirms
`checkCollision`/`checkArcCollision`/`raycast`/`rebuildSpatialGrid`/
`isOutsideCell` are all absent from the diff, and the only reads of
`activeCell.radiusX/radiusY` (the real collision boundary) in the new code are
reads, never writes -- §7.6's regression sweep doesn't apply. `sw.js`
`CACHE_NAME` bumped v44->v45; `dist/` rebuilt (`--check` passes).

**Section 5 (hazard colour language table), landed 2026-08-14.** Read every
hazard's draw code (not just the intro list's seven names) to build the rule
before touching anything, per the section's own instruction. Two families:

| Family | Rule | Hazards | Colours (function) |
|---|---|---|---|
| **Always-lethal** ("saturated, alive") | never breakable, any mode | Membrane wall | `0x1e3799`/`0x4a69bd`/`0x82ccdd` (`drawCalcification()`) |
| | | Nucleus core | `0x4834d4`/`0x6c5ce7`/`0xa29bfe`/`0x686de0` (nucleus draw block) |
| | | Live mitochondrion | `C_MITO 0x2ecc71`, core `0x55efc4` |
| | | Live lysosome | `0xff4757` ring, `0xff6b81` bubble |
| | | ER / Golgi walls | `0x0abde3` (ER), `GOLGI_COLOR 0x8c7ae6`, arcs `0x4a69bd`/`0x1e3799` |
| | | Mitosis scaffolding + death ring | wall `0x4a69bd`, sweep `0xff4757` (`drawMitosisVisuals()`) |
| | | Infection virus particles | `0xff4757` body (`drawInfection()`) |
| | | Necrotic debris (shrapnel) | `0x8899aa`/`0x3c4a52` -- **exception, see below** |
| | | Player traces | per-player assigned colour |
| **Breakable in attack mode** ("desaturated, mineral") | `p.targetMode === 'attack'` breaks it instead of killing (`updatePlayers()` 1.6/1.7, `checkCollision()`'s `org.necrotic` branch) | Necrotic organelle / cluster | `0x707070`/`0x9a9a9a` (organelle), `0x5a6b78` fill / `0x2c3a42` outline (`drawNecroticClusters()`) |
| | | Malignant mass / aggregate | `0x8a6d2f` steady, `0xffe6a8` fresh-block flash (`drawMalignantMass()`) |
| | | Nucleus chaser | was `0xff4757`/`0xff6b81` -- **identical to the live lysosome above** -- now `0xad5a72`/`0xc97e93` (`drawNucleusChasers()`) |

The one real violation the codebase had: nucleus chasers (breakable, T57) reused
the live lysosome organelle's exact ring/bubble hex pair (`0xff4757`/`0xff6b81`),
so a player could not tell the two apart by colour even though one always kills
and the other can be cleared in attack mode -- the opposite of what this section
asks the palette to communicate. `0xff4757` turned out to be the game's
established "lethal red" (also the virus body, the mitosis death-ring sweep, and
the ribosome-studding colour), which the chaser broke by borrowing for a
breakable hazard; nothing else in the always-lethal column needed to change.
Fixed by recolouring the chaser (`drawNucleusChasers()`, and the matching
`destroyNucleusChaser()` break-particle burst) to `0xad5a72`/`0xc97e93` -- a
dusty rose roughly 34-41% as saturated as the original neon pair by HSL (down
from ~90%+), landing in the same desaturated register as the necrotic
grey-blue and aggregate amber while keeping its own distinct hue so the three
breakable hazards stay distinguishable from each other, not just from the
always-lethal set.

Checked every other breakable-family hex (`0x707070`, `0x9a9a9a`, `0x5a6b78`,
`0x2c3a42`, `0x8a6d2f`, `0xffe6a8`, `0xffdf9e`) against the whole file by grep --
none collide with an always-lethal hazard.

**Exception, not fixed:** necrotic debris (`drawNecroticDebris()`, shrapnel shed
by necrotic clusters, `checkCollision()`'s own comment: "lethal, not breakable")
is tonally a grey-blue close to the breakable necrotic cluster's mineral
palette, which is the family the rule says it should visually *not* share with
being always-lethal. Left as-is: it's shed *from* the breakable cluster, so the
family kinship reads as intentional lineage rather than a "can I break this"
signal in practice, its fast/sharp fragment silhouette is already unlike the
static cluster's blob shape, and no confusion with it surfaced in any check
this session (screenshots, real rounds). Recolouring an existing, unambiguous
hazard on a hypothesis rather than an observed problem risks §1.2 scope creep;
noted to `docs/BACKLOG.md` for a future session's judgement call instead.

Verified: close-up (zoom 2.0) and true-playing-zoom (0.55) screenshots with a
forced lysosome organelle and a forced chaser framed together show the chaser
now reading as a muted dusty-rose dart against the lysosome's vivid coral-red
ring -- no longer colour-identical. `drawNucleusChasers()` cost measured at
0.0127ms/call (3000 calls, 5 chasers, after a 50-call warmup) -- a straight
constant swap, no new draw calls or allocations, negligible against the 16.6ms
frame budget. `worldChildren` flat at 16. A real 15.1s round (1 human + 3 bots,
non-immortal) played normally, human died as expected with no input, console
clean. An offline `file://` load of the rebuilt `dist/Cellular_Zatacka.html`
(8.2 game-seconds, immortal) also console-clean. `git diff` confirms
`checkCollision`/`checkArcCollision`/`raycast`/`rebuildSpatialGrid` are all
absent from the diff -- purely a draw-colour change, §7.6 doesn't apply. Not
tier-gated: it changes which constant two existing fills use, not a new draw
call or particle count to gate, same reasoning as sections 2-4's `zoomBoost`/
parallax. `sw.js` `CACHE_NAME` bumped v45->v46; `dist/` rebuilt (`--check`
passes).

Section 6 remains unstarted.
