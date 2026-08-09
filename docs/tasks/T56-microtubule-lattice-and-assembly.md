# T56 — Make the trace read as a microtubule, and animate it assembling

**Track:** K · **Depends on:** T42, T47 · **Risk:** medium (touches the T25 bake path) · **Est. diff:** ~120 lines

Owner report, 2026-08-09, with a screenshot: *"this is how the 'microtubule'
version looks now so it does not look too similar and I would like to have this
small tubulin animation coming in together at the front 'assembling' it."*

**Do T47 first.** It is a listed dependency for a reason: at the camera zooms
T47 measured (0.17–0.44 in shared camera) none of this work is visible at all,
and you would be tuning a look nobody can see.

---

## What is on screen now

T42 stamps two small circles per settled trace edge, offset either side of the
centreline, with the pair's colours swapping every `DIMER_SPACING` world px. At
the growing tip the last 12 points get the same motif with a sine pulse.

The result — see the owner's screenshot — is a **single-file chain of beads**. It
reads as a string of pearls, not as a polymer tube. The alternation is there but
at these sizes the two offset circles merge into one blob per step, so the α/β
distinction is invisible and the width never suggests a tube.

## What a microtubule actually looks like

> **Assumption flag.** The owner linked a YouTube animation
> (`youtube.com/watch?v=JTN5ZliJ-yk`). This session's egress policy hard-blocks
> youtube.com, so it was **not** watched. The description below is standard
> microtubule structure, not that specific video — if the reference differs,
> the owner should say so before this is tuned.

The features that make the shape recognisable, in rough order of how much they
buy per pixel:

1. **It is a tube, not a line.** 13 protofilaments arranged in a hollow
   cylinder. In 2D, that reads as a **band with parallel longitudinal lines**
   running along it — 3 or 4 lines is enough to suggest 13.
2. **The subunits are staggered, not aligned.** The helical lattice offsets
   each protofilament slightly against its neighbour, giving a **brick-wall /
   diagonal seam** pattern rather than clean rungs.
3. **α and β alternate along each protofilament.** Two tones, repeating — which
   T42 already has, it is just not legible at one bead per step.
4. **The growing end is flared.** Protofilaments splay outward at the tip like an
   opening flower before closing into the tube behind. This is the single most
   recognisable frame of any assembly animation.
5. **Free dimers in the surroundings dock onto that tip.** They arrive, land, and
   the tube extends. This is the animation the owner is asking for.

## The work

### A. Lattice instead of a bead chain (baked)

Replace the two-circle stamp with a band:

- 3–4 longitudinal lines along the trace direction, spanning `TRACE_WIDTH`, so it
  reads as a tube wall rather than a centreline.
- Subunit blocks along each line, **offset between adjacent lines** so the seam
  runs diagonally. Keep the α/β two-tone from T42, keyed off the same stored `.d`
  so the pattern stays stable no matter how many points a frame appends.
- Keep it deterministic. Any jitter must be hashed from `.d`, never
  `Math.random()`, or the baked texture will shimmer against itself.

**Constraint that governs everything here:** this is baked once into the
RenderTexture (T25, append-only) and never redrawn. Cost per appended edge may go
up a little; cost per *existing* trace length must stay zero. If you find
yourself wanting to redraw settled trace, stop — that is T25's whole point.

`TRACE_HITBOX` and every collision path stay **exactly** as they are. This task
is rendering only, and the commit message must say so explicitly.

### B. The flared tip and assembly (per frame, bounded)

The tip is already redrawn every frame into `trailCore` for the last
`TIP_POINT_COUNT` points — that is the right place, it is bounded regardless of
trace length, and nothing there is baked.

- **Flare:** widen the band over the last few points and splay the outer
  protofilament lines away from the centreline, largest at the very tip. Even a
  small splay reads instantly as "growing end".
- **Incoming dimers:** a handful of free subunits drifting in toward the tip, each
  snapping onto it and disappearing as the tube reaches them. Cap it hard —
  `ASSEMBLY_DIMERS_MAX`, something like 6–8 per player.
- **Reuse T17's pooled emitter if it can express this**; if the docking motion
  genuinely cannot be expressed as a particle with a velocity and a lifetime,
  keep the state as a small fixed-size array on the player, allocated once at
  round start and reused. **Do not build a second particle system** — the same
  line T42 was given, and it still applies.
- T42 already scatters dimers outward when a red vesicle is collected
  (depolymerisation). Assembly is the mirror of that; make the two obviously the
  same material moving in opposite directions.

### C. Keep it working where it is actually seen

- Split-screen (fixed 0.6 zoom) is where the owner plays most. Tune there first.
- Respect the quality tiers: on `low`, drop to fewer protofilament lines and
  fewer incoming dimers rather than switching the look off entirely.

## Verification

1. Console clean.
2. **Screenshots at `world.scale.x` ≈ 0.6, 0.9 and 1.5**, each next to the
   current build's equivalent. The band must read as a tube, and the seam must be
   visible, at 0.6.
3. **Tip flare and incoming dimers visible in motion** — a short frame sequence
   (3–4 screenshots across ~1s) showing a dimer approach and the tube extend.
4. **Per-frame `drawTraces()` cost still flat** at 15/30/60/120 game-seconds.
   This is the measurement T25 and T42 both had to pass and it is the one that
   catches a mistake here.
5. **Bake cost per appended edge** stated in `## Findings`, before and after.
6. **Collision completely unchanged** — `TRACE_HITBOX`, `rebuildSpatialGrid`,
   `checkCollision` untouched; prove with a head-on trace collision at Very Fast
   under 4× fuzzer dilation.
7. Dimer count never exceeds `ASSEMBLY_DIMERS_MAX`; `particleCount` still under
   `MAX_PARTICLES` with four players assembling at once.
8. `worldChildren` flat over 10 minutes; RT memory unchanged.
9. Quality tiers: screenshot `low` and `high`; `low` must still be a tube.
10. Regression sweep §7.6.

## Definition of done

- [ ] Lattice band with staggered subunits and a visible seam, baked, deterministic
- [ ] Flared growing tip
- [ ] Incoming dimers docking, capped, no second particle system
- [ ] Collision untouched and proven
- [ ] `drawTraces()` cost flat; bake cost stated
- [ ] Legible at 0.6 zoom (split-screen) — screenshots at three zooms
- [ ] `docs/TASKS.md`: T56 → `DONE`

---

## Findings

*(Before/after screenshots at each zoom; the assembly frame sequence; bake cost
per edge before and after; how the incoming dimers are stored.)*
