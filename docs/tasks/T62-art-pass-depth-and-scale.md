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
- [ ] Section 2 — membrane low-zoom treatment
- [ ] Section 3 — mitosis bridge as a curve, not four straight lines
- [ ] Section 4 — depth (parallax, edge falloff)
- [ ] Section 5 — hazard colour language table
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

Remaining sections (2-6) are unstarted.
