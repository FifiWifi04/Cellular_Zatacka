# T47 — The tubulin motif is invisible in shared camera: zoom never reaches the LOD gate

**Track:** J · **Depends on:** T42 · **Risk:** medium (touches camera framing
*or* trace RT resolution — both are things players notice) · **Est. diff:** ~40 lines

Owner report, 2026-08-09: *"I don't see the microtubules graphics."* Part of
that was a stale download — T42 landed after the build they had. But it is not
the whole story: **in shared camera the motif is off almost all of the time.**

---

## Measurement

T42 gates the dimer motif on `world.scale.x >= DIMER_LOD_ZOOM` (0.5), because
below that it aliases into noise — `TRACE_RT_SCALE` is a fixed fraction of world
pixels regardless of camera zoom, so a `TRACE_WIDTH*0.35` dimer offset
rasterises to sub-pixel detail in the RT before the camera ever sees it. That
reasoning is sound and is documented in T42's `## Findings`.

What was not measured is **what zoom actually occurs in play.** Sampled every
60 ms over a full round, godMode, no human input:

| Config | zoom min | zoom max | ever ≥ 0.5? |
|---|---|---|---|
| Phone 844×390, shared, 2 players | 0.193 | 0.737 | briefly, at spawn |
| Phone 844×390, shared, 4 players | 0.166 | **0.441** | **never** |
| Phone 844×390, split-screen | 0.600 | 0.600 | always (fixed `splitZoom`) |
| Desktop 1280×800, shared, 4 players | 0.479 | 1.135 | briefly, at spawn |

Shared camera has **no lower clamp**:

```js
let targetZoom = Math.min((app.screen.width - 200) / distX,
                          (app.screen.height - 200) / distY, 1.2);
```

`distX`/`distY` is the bounding box of living players, so the moment they
separate the camera pulls back without limit. On a 390px-tall viewport,
`h - 200 = 190` — players 400 world-px apart already put the zoom under 0.48.
The four-player phone round never once crossed the threshold, so its trace was a
plain line for its entire duration.

So T42's headline visual is on only in split-screen and in the first seconds of
a shared round. Note also that T42 bakes the LOD decision per-bake, on purpose,
so a stretch drawn while zoomed in stays beaded — that part is fine and should
not be changed.

## The choice to make

Pick **one** and say why in `## Findings`. Do not do two.

1. **Floor the shared-camera zoom** (recommended). Clamp `targetZoom` to a
   minimum of ~0.5 and let players who separate beyond that go off-screen — that
   is what split-screen already exists for. This also fixes a readability
   problem that has nothing to do with the trace: at 0.166 the entire arena is
   rendered at a sixth scale, and organelles, vesicles and the aggregate are all
   correspondingly tiny. Verify that a player leaving the view is survivable and
   that the bots do not immediately die off-screen.
2. **Raise the trace RT resolution when zoomed out**, so the motif stays
   resolvable and the LOD gate can be lowered. Costs RT memory — measure it, and
   respect the T25 rule that already-composited content is never re-baked.
3. **Scale the motif in world units as zoom falls** (bigger beads, wider
   `DIMER_SPACING` when zoomed out). Cheapest, but the beads then change size
   relative to the trace, which may read as a different material rather than a
   zoom level. Screenshot before committing to it.

Whichever is chosen, the LOD fallback itself stays — it is the correct structure.

## Verification

1. Console clean.
2. Re-run the zoom sampling above for all four configs and put the new table in
   `## Findings`. The motif must be on for the **majority** of a shared-camera
   round on a 844×390 viewport, not just at spawn.
3. Screenshots at the new zoom floor (or new RT scale) at 2 and 4 players — the
   beads must read as a polymer, not as noise. This is the whole point of the
   task; if they alias, the option chosen was wrong.
4. `drawTraces()` per-frame cost still flat at 15/30/60/120 game-seconds (T25's
   measurement, which T42 also had to pass).
5. If option 1: a player driven off the visible area still steers, still dies to
   what it hits, and bots do not degrade. 2 minutes at Gen 2.
6. If option 2: `worldChildren` flat and RT memory stated in `## Findings`.
7. Split-screen unaffected (already fixed at 0.6).
8. Regression sweep §7.6.

## Definition of done

- [ ] One option chosen, with the reasoning in `## Findings`
- [ ] Motif visible for most of a shared-camera round at 844×390 — new zoom
      table committed
- [ ] Screenshots at 2 and 4 players
- [ ] `drawTraces()` cost still flat
- [ ] `docs/TASKS.md`: T47 → `DONE`

---

## Findings

*(Which option, why, the new zoom/coverage table, and the screenshots.)*
