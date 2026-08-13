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

## Findings

*(Per section: what was done, the screenshots, the cost measurement.)*
