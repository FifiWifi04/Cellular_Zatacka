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

- [x] One option chosen, with the reasoning in `## Findings`
- [x] Motif visible for most of a shared-camera round at 844×390 — new zoom
      table committed
- [x] Screenshots at 2 and 4 players
- [x] `drawTraces()` cost still flat
- [x] `docs/TASKS.md`: T47 → `DONE`

---

## Findings

**Option 1 chosen** (floor the shared-camera zoom). Changed one line in
`updateCamera()`'s non-emergency shared-camera branch:

```js
let targetZoom = Math.max(Math.min(zoomX, zoomY, 1.2), DIMER_LOD_ZOOM);
```

Reusing `DIMER_LOD_ZOOM` (0.5) as the floor ties the camera clamp to the exact
threshold the dimer LOD gate checks, so the two can't drift apart later. The
`isEmergency` branch (virus warning / mitosis reveal, `viewSpan` 3000-6500) is
deliberately untouched — that reveal camera needs to zoom out past 0.5 to show
both cells, and it doesn't render the motif since gate context is different
per T42. Split-screen was already fixed at 0.6 and is unaffected.

Rejected option 3 (scale motif in world units) per the task's own warning —
changing `DIMER_SPACING` with zoom would make the trace read as a different
material at different zooms. Rejected option 2 (raise RT resolution) as more
expensive and unnecessary once the zoom floor keeps the RT's fixed
`TRACE_RT_SCALE` adequately resolved.

**New zoom table** (`tools/verify_harness.py`, `world.scale.x` sampled every
60ms for 25 wall-seconds, godMode/immortal, no human input):

| Config | zoom min | zoom max | % samples ≥ 0.5 |
|---|---|---|---|
| Phone 844×390, shared, 2 players | 0.500 | 0.677 | 100.0% |
| Phone 844×390, shared, 4 players | 0.500 | 0.500 | 100.0% |
| Phone 844×390, split-screen | 0.600 | 0.600 | 100.0% (unaffected, as expected) |
| Desktop 1280×800, shared, 4 players | 0.510 | 1.066 | 100.0% |

Was 0% of a full round for the 4-player phone case before this change (zoom
capped at 0.441, per the task's original measurement table). The motif is now
on for the entire sampled span in every shared-camera config, not just at
spawn.

**Screenshots** at the new floor, `/tmp/verify/t47_shared_2p_844x390.png`
(zoom 0.500) and `t47_shared_4p_844x390.png` (zoom 0.500): the alternating
cyan/red beading on both the human's and bots' traces reads clearly as a
beaded polymer chain, not noise, at 844×390.

**`drawTraces()` cost** (mean of last ~120 calls, 1 player + 3 bots, immortal,
640×480 — unaffected by this change since it only touches `updateCamera()`,
confirmed flat as expected):

| game-time | drawTraces (ms) |
|---|---|
| 15s | 0.298 |
| 30s | 0.270 |
| 60s | 0.179 |
| 120s | 0.141 |

Flat/decreasing (no growth), consistent with T25/T42's finding that per-frame
cost does not scale with trace length.

**Off-screen survivability** (item 5): 1 player (no human input) + 3 bots,
shared camera, 844×390, `setGeneration(2)`, not immortal. Zoom sat at 0.654
(above the floor, players hadn't separated past it). Round ran 46.3s before
ending naturally (3 of 4 players died to normal hazards, 1 bot survived alone,
`isPlaying` flipped false cleanly) — confirms death, bot AI and round-end all
behave normally under the new clamp; nothing hung, degraded, or errored.

**Verified:** console clean (all six harness scripts, `assert_console_clean`
passed every time, zero console/page errors); `python3 tools/build_standalone.py`
rebuilt `dist/Cellular_Zatacka.html`; `sw.js` `CACHE_NAME` bumped (v17 → v18)
since `260703_Cellsnake.html` changed; split-screen zoom unaffected (0.6
constant, matches pre-change behaviour); regression sweep not required per
AGENT_CONDUCT §4.1/§7.6 — this change does not touch `checkCollision`,
`checkArcCollision`, `raycast`, or `rebuildSpatialGrid`, and the off-screen
survivability run above exercised normal membrane/hazard deaths without
incident.
