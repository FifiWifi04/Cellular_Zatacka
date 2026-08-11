# Task Board — Cellular Zatacka

Sequential work plan. **Do one task per session, in order.** Read
[`AGENT_CONDUCT.md`](AGENT_CONDUCT.md) first — every time.

Target file: `260703_Cellsnake.html` (single file, no build step).

---

## How to use this board

> ## ⚠️ PRIORITY OVERRIDE (2026-08-07)
> **Take Track J (T33–T37, T40) before anything else, starting with T33.**
> These are defects the owner hit in real play. They outrank the normal
> lowest-numbered rule, which would otherwise send you to T22 — a large
> refactor — while shipped bugs sit unfixed.
>
> Order: **T43 → T40 → T44 → T39**, then Track K as it unblocks, then T22 and
> Phase 7. (T33–T37, T40, T43, T44, T45 and T39 are done — T43 landed
> 2026-08-08, the blue vesicle's Golgi-pass now actually works; T45 was fixed in
> an owner session the same day; T44 landed 2026-08-08, viewport AA/downscale
> tiering plus a probe-gated MSAA fallback for backends that silently fail to
> resolve it; T39 landed 2026-08-08, the "tumour" is now a protein aggregate
> with organic amber-blob visuals and generation-scaled growth — see
> `docs/tasks/T44-splitscreen-quality-and-cost.md` Findings for T44.) **Track J
> is fully done. T38 landed 2026-08-09 — necrotic organelles now fuse, shed
> lethal debris that scales with cluster size, and break apart one member at a
> time in red mode; see `docs/tasks/T38-make-necrosis-matter.md` Findings.
> **Track K is now fully done** — T42 (tubulin-dimer trace) landed 2026-08-09,
> see `docs/tasks/T42-tubulin-trace.md` Findings.
>
> **Owner session 2026-08-09 reopened Track J.** T46 (Help did not pause) is
> already fixed. Order from here:
>
> Original order was **T50 → T48 → T49 → T47 → T56 → T51 → T52 → T57 → T22 →
> Track L → Phase 7**; everything up to and including T57 has now landed (see the
> notes below).
>
> **T58 landed 2026-08-10** — `isOwnNeck()` now compares a stable per-segment id
> (`newTraceSegment()` stamps `player.nextSegId++` at every segment-creation
> site, including `removeFrontPoints()`'s empty-array placeholder) instead of
> the segment's index in the mutable `traceSegments` array, so `shift()`/`splice()`
> from a redirected lysosome pickup or the 50% wipe can no longer desync the
> spatial grid's self-immunity check. The two prior commits on this branch had
> only filed the task and re-confirmed the repro, not implemented the fix.
> Verified: the exact repro (P1 attack, lysosome onto P1's head, redirected to
> P2) no longer kills — P2's segments still drop 2→1 but P2 stays alive, and the
> mirror direction (P2→P1) is unaffected too; the 50% wipe still cuts a
> real 24-point trace to 13 without killing the owner; self-immunity holds at
> all 3 speeds (no false deaths, dies at ~1.1s exactly when a tight loop closes
> on itself); a real 3-bot round ran 73.1s clean, and a 330-wall-second fuzzer
> burst (godMode off, so collision stayed live) completed 140 full round
> cycles with 0 errors. `i`/`segLength` (write-only, unread) were deleted
> rather than made stable. `sw.js` `CACHE_NAME` bumped v22→v23; `dist/` rebuilt.
> See `docs/tasks/T58-red-vesicle-instakills-opponent.md` Findings.
>
> **T22 landed 2026-08-11 — all 7 steps done, see the Track G notes below.**
> Next up: **Track L** (Phase 8, starting with T53, already `READY`), then
> Phase 7 starting with T28 (now `READY`). Phase 9
> (`PHASE9-LATE-GAME-ARC.md`) is scoped but deliberately has no task files until
> T52/T57 have been played.
>
> **T50 landed 2026-08-09** — grey matter is never lethal in attack mode now,
> lone or clustered, cooldown or not; see `docs/tasks/T50-red-mode-necrosis-inconsistent.md`
> Findings.
>
> **T48 landed 2026-08-09** — deleted the rectilinear grid-edge outline (the
> overlapping blob circles already read as one silhouette) and added a cull
> pass in the calcification block that drops aggregate blocks once the
> shrinking membrane retreats past them, respawning the aggregate if every
> block is culled; see `docs/tasks/T48-aggregate-grid-outline-and-containment.md`
> Findings.
>
> **T49 landed 2026-08-09** — membrane protrusions and `cellBg` now re-anchor
> to the current (post-calcification) radii every frame the radii actually
> change (28/28 protrusions now sit exactly on the wall, mean ratio 1.0, both
> mid-shrink and at the floor — was 28/28 outside, mean radius 1304 vs a wall
> at 1249), and drifting cytosol blobs are pulled back inside the ellipse the
> instant they'd cross it (0/226 outside at every measured point). Per-frame
> cost of the re-anchor: 0.0085ms with the radii-unchanged early-out. See
> `docs/tasks/T49-membrane-furniture-follows-shrink.md` Findings.
>
> **T47 landed 2026-08-09** — shared-camera zoom is now floored at
> `DIMER_LOD_ZOOM` (0.5) in `updateCamera()`'s non-emergency branch, so the
> tubulin-dimer motif (and the rest of the arena) no longer shrinks to noise
> once players separate; players beyond the floor go off-screen instead,
> same as split-screen already allows. Motif now on 100% of sampled time in
> every shared-camera config tested (was 0% for the 4-player phone case);
> `drawTraces()` cost still flat; off-screen deaths/round-end behave
> normally. See `docs/tasks/T47-dimer-lod-never-reached.md` Findings.
>
> **T56 landed 2026-08-09** — the trace motif is now a lattice band (2-4
> tier-driven longitudinal lines with a staggered, phase-shifted colour seam)
> instead of T42's two-dot bead chain, the growing tip flares outward at
> `TIP_FLARE_MAX=1.1` right at the point, and free tubulin dimers spawn near
> the tip and drift in to "dock" (reusing T17's particle pool, hard-capped at
> `ASSEMBLY_DIMERS_MAX=8`/player via an exact owner-tracked counter, not just
> spawn cadence). `drawTraces()` steady-state cost stayed flat (0.20-0.32ms)
> across a 7.7x trace-length increase (692→5340 points); collision proven
> byte-identical (same 4.1s membrane-death figure as T42's own check).
> See `docs/tasks/T56-microtubule-lattice-and-assembly.md` Findings for full
> numbers, including where 60/120-game-second real-time measurement had to be
> substituted with a synthetic-length methodology under this session's time
> budget.
>
> **T51 landed 2026-08-10** — ATP granules (Gen 2+, own array, spawn-biased
> to the outer `ATP_ANNULUS_FRAC`(0.72) band of the current wall) pause the
> shared membrane shrink for `ATP_PAUSE_DURATION`(4s) per pickup, capped at
> `ATP_PAUSE_MAX`(12s); membrane glows and a HUD bar reads out the remaining
> pause. Proven over a real (non-synthetic) 210-game-second Gen 2 run with 3
> bots and `godMode` on: wall reached `CALCIFY_FLOOR` at 142s despite at
> least one confirmed bot pickup mid-run; granule count held at ≤6
> (`ATP_MAX`) throughout; `worldChildren` flat at 15 (no leak). Collision
> regression sweep at all three speeds passed via direct `checkCollision()`
> calls (raycast/rebuildSpatialGrid were touched to add the new reward
> channel). See `docs/tasks/T51-slow-the-calcification.md` Findings; two
> incidental issues (mitosis snap's kill check still gated on `devMode`
> instead of `godMode`; `atpGranules` not rescued at the snap like the other
> hazard arrays) filed to `docs/BACKLOG.md`, both out of scope here.
>
> **T52 landed 2026-08-10** — vesicles now carry a `freeUntil` field (3.0s at
> meter 0, shrinking to 0 past 85% of `NUCLEUS_FEED_MAX`); every vesicle the
> Gen 4+ well actually pulls into the nucleus adds its type's weight
> (membrane 8 / mitochondria 12 / lysosome 18, out of `NUCLEUS_FEED_MAX=850`)
> to a new shared, monotonic feed meter shown as a responsive DOM HUD bar,
> with a per-consume inward particle burst + nucleus flare + HUD glow, plus a
> one-off establishing pulse the first frame Gen 4 is reached. No new hazard
> was added (the nucleus core was already lethal in both `checkCollision()`
> and `raycast()` via T15), so the §4.1/§7.6 collision rules don't apply here
> — confirmed neither function appears in the diff. Denial proven two ways:
> a 90-simulated-second synthetic run (parked 512/850 vs. omniscient
> collecting 0/850) and real 3-bot gameplay (feed 12/850 at 45s with 3 bots
> active vs. 34/850 with none). Meter reaches max in ~165.7s if ignored
> (tuned near Gen 2's ~128s calcification-floor time); bots played a real
> 120.1-game-second Gen 4 round with 3/3 alive (no nucleus suicides) and flat
> `worldChildren`; forced peak-consume burst capped `particleCount` at
> exactly `MAX_PARTICLES`. Well legibility fixed by scaling ring
> stroke/alpha by `1/world.scale.x` (uncapped — the previous T47-floor clamp
> would have under-scaled at the 0.2-zoom case this task specifically asks
> for); screenshotted legible at 0.2/0.4/1.0 zoom and the bar at
> 390×844/844×390/1280×800. One incidental pre-existing bug (the pause/start
> menu not fully leaving short/narrow viewports despite `hidden-ui`,
> reproduced on the pre-T52 commit) filed to `docs/BACKLOG.md`, out of scope.
> See `docs/tasks/T52-gen4-nucleus-feeding.md` Findings for full numbers.
>
> **T57 landed 2026-08-10** — when the Gen 4 nucleus-feed meter (T52) maxes,
> the cell "turns": a 3s freeze/reveal (reusing the existing `isCellFrozen`
> path, screenshake, a particle burst, a banner), then after a 4s grace period
> the nucleus spawns homing "chasers" (called that, not "hunters", to avoid
> colliding with the pre-existing player Hunter Mode power-up) capped at 5,
> lifetime 20s, speed 60px/s — slower than the player at every actual speed
> setting (90/150/210px/s) — with a turn-rate cap so they're steerable around,
> not a perfect tracker. Lethal via a new inline swept block in `gameLoop`
> (mirroring T14's malignant-mass pattern, not `checkCollision()` itself) and
> sensed via `raycast()`/`spatialGrid`; breakable in attack mode with a
> cooldown that declines the break without killing (T50's exact rule, applied
> from the start). Survivability model (b): after 90s of the active state,
> spawning stops for the rest of the round. Verified: freeze holds a parked
> player's position exactly; grace period keeps the arena chaser-free for a
> full 7s after the meter maxes; self/attack-mode/cooldown-decline behaviour
> confirmed via direct `gameLoop()` calls; caps/lifetime held under stress
> probes; 3 real 3-bot trials measured 26.8-57.6s (mean 45.3s) survival after
> transformation; console clean and `worldChildren` flat (15→16, the one new
> layer) throughout. See `docs/tasks/T57-transformed-nucleus.md` Findings for
> full numbers and the naming-collision/checkCollision-scope reasoning.
> **T22 (resumable) is in progress.** Step 1 (vesicles) landed 2026-08-10; Step 2
> (infection/virus split, `updateInfection()`/`drawInfection()`, a new
> `infection.warningVisible` field to preserve the hexagon-glyph's exact
> on-breach-frame timing) landed 2026-08-10 too — see
> `docs/tasks/T22-sim-render-split.md` Findings. **Step 3 (organelles split)
> landed 2026-08-10** — `updateDriftingOrganelles()` is now state-only (the
> `o.rotation` advance is unconditional, no longer gated on `o.sprite`) and a
> new `drawOrganelles()` mirrors `sprite.x/y/rotation` and the necrotic
> freeze-flicker alpha; a 30s immortal round found 0/25 sprite-mirror
> mismatches, forced-Gen-2 necrosis flicker still verified correct, and a real
> non-immortal round played normally. **Step 4 (mitosis split) landed
> 2026-08-10** — the three named state mutations (`centralHitboxes = []`,
> `mitosis.nucleusDestroyed = true`, the `spawnVesicles()` burst) moved from
> `drawMitosisVisuals()` into `updateMitosis()`, gated by a state-only
> `crossedCenter && !mitosis.nucleusDestroyed` check (replacing the old
> `nucleusLayer.visible` display-object read); `mitosis.nucleusDestroyed` is
> now reset at the snap (mirroring `generateMap()`'s pre-existing implicit
> reset of `nucleusLayer.visible`) so a second mitosis event can still destroy
> its own nucleus, which a naive move would have silently broken.
> `drawMitosisVisuals()` now just mirrors `nucleusLayer.visible =
> !mitosis.nucleusDestroyed`. Verified via direct-state forcing (both the
> single-event trigger and a forced snap + second event), screenshots before/
> after the forced crossing, a real 30.2s round, and a `file://` load — see
> `docs/tasks/T22-sim-render-split.md` Findings.
>
> **Step 5 (players/traces split) landed 2026-08-11** — the old fused
> `gameLoop` `players.forEach` (bot AI, every swept collision check, vesicle/
> ATP pickup, trace append/gap management, the mitosis death-ring sweep) moved
> verbatim into a new `updatePlayers(delta, deltaSec, isCellFrozen)`; only the
> uiBarsLayer status bars were pulled out, into a new `drawPlayerBars()`. The
> four per-player bars needed a value snapshot (`p.barX/barY/barGhostTimer/
> HunterTimer/GolgiTimer/SpeedTimer/SpeedLevel`), not just a cut-and-paste,
> since the old code drew them mid-iteration using pre-pickup values — reading
> `p.effects.*` fresh after `updatePlayers()` finishes would have shown
> post-pickup values a frame early. The global ATP bar needed no snapshot (the
> original already drew it once, after every player had been processed).
> Verified: brace-matched extraction of `updatePlayers()` shows zero
> `PIXI`/`Layer`/`.sprite`/`.visible` references; a real 30.2s round (1 player
> + 3 bots) played normally; membrane/self-trace/organelle deaths and vesicle/
> ATP pickup all confirmed via direct state-forcing, including proof the bar
> snapshot ordering fix works (pickup-frame bar still shows the pre-pickup
> value, next frame shows post-pickup); 15s real rounds at all three speeds
> clean. One pre-existing violation noted to `docs/BACKLOG.md`:
> `updatePlayers()` isn't fully PIXI-free (`destroyNecroticOrganelle()` inside
> it touches `organellesLayer`/`.sprite`, a T13/T38/T50-era coupling predating
> this split). See `docs/tasks/T22-sim-render-split.md` Findings.
>
> **Step 6 (`gameLoop` restructured into `stepSimulation`/`renderFrame`) landed
> 2026-08-11** — the remaining fused code (calcification, screenshake,
> necrosis-promotion, the mitosis death-ring shatter) got the same state/draw
> split as everything else, letting the whole frame regroup into
> `stepSimulation(delta)` (state; returns `{ended:true}` on the two round-end
> paths so `gameLoop` skips rendering that tick, matching the old code's own
> early `return;`s) and `renderFrame(isCellFrozen, deltaSec)` (pure reads).
> Verified: `stepSimulation()`'s own 320-line body has zero `PIXI`/`Layer`/
> `.sprite`/`.visible` tokens outside one comment; a real 30.2s round played
> normally; a forced-frozen check held `globalRotation` and organelle/vesicle
> counts completely flat across 1.5+ game-seconds (and reproduced the same
> small artefact-drift on pre-step-6 `HEAD` when tested the same way, ruling
> out a regression); membrane/self-trace/organelle deaths all still lethal;
> 15s rounds clean at all three speeds; the fuzzer's own round-restart path
> and a natural round-end both exercised with no console errors. Two new
> helpers (`destroyOrganelleSprite`/`attachOrganelleSprite`) keep
> `stepSimulation()`'s own text free of `Layer`/`.sprite` references while the
> necrosis-promotion and death-ring-shatter blocks that call them remain not
> fully PIXI-free (same class of exception as step 5's, both filed to
> `docs/BACKLOG.md` along with the background-elements block, which stayed
> fused and out of scope since `cytosolParticles`/`membraneProtrusionsList`
> entries are themselves `PIXI.Graphics` instances with no separate physics
> record to split). See `docs/tasks/T22-sim-render-split.md` Findings.
>
> **Step 7 (headless step loop exposed and benchmarked) landed 2026-08-11 —
> T22 is now fully `DONE`.** `window.stepHeadless(seconds, dt)` fixes a bug in
> the task's own pseudocode: `stepSimulation()` reads `deltaSec` from
> `app.ticker.deltaMS`, not from its `delta` parameter, and `delta` itself is
> PIXI frame-units (`≈ dt_seconds * 60`, not seconds) — so a naive
> `stepSimulation(dt)` loop would leave `deltaSec` frozen at a stale value and
> under-drive every `delta`-scaled quantity 60x. The fix sets
> `app.ticker.deltaMS = dt * 1000` and calls `stepSimulation(dt * 60)` per
> iteration, matching what a real tick at that rate would produce, and stops
> early on `{ended:true}`. `Game.run_headless_seconds()` added to
> `tools/verify_harness.py`. **Speedup measured: 17.5x** — 30 game-seconds
> headless in 4.01 wall-seconds (7.53x real time) versus the same 30
> game-seconds through the rendered loop in 70.63 wall-seconds (0.43x real
> time, matching the harness's documented ~0.38x at 640x480). A 10s immortal
> headless run advanced `survivalTime` by 10.2s and produced 2209 trace points
> with `worldChildren` unchanged (16, same as an equivalent rendered round) and
> console clean; a screenshot taken immediately after showed a fully-formed,
> undistorted scene once a real frame caught up. A real (non-headless) 30.2s
> round played normally afterward, and an 8.2s headless run over `file://`
> (offline, `dist/`) also completed clean. `dist/` rebuilt (`--check` passes);
> `sw.js` `CACHE_NAME` bumped v29→v30. See
> `docs/tasks/T22-sim-render-split.md` Findings for full numbers.
>
> **T28 (fixed-timestep simulation) is now `READY`** — its only dependency,
> T22, is fully done.

1. Open this file. Find the lowest-numbered task with status **`READY`**,
   **subject to the priority override above**.
2. Open `docs/tasks/<ID>-*.md` and follow it exactly.
3. When done and verified, change that task's status here to **`DONE`**, and
   change the next task's status from `BLOCKED` to `READY` **only if** its listed
   dependencies are all `DONE`.
4. Commit both the code change and this board update together.

Statuses: `READY` · `BLOCKED` (dependency not met) · `DONE` · `PARKED` (deferred
by owner decision) · `OWNER-RUN` (must be run by a human, not a scheduled agent).

**When you add a new task that depends on an existing one, go update that
task's `Definition of done` checklist** so it flips your new task to `READY`.
A dependency recorded only in this table is invisible to the session that
completes the upstream task — that is how T22 sat `BLOCKED` for days with its
dependency long since satisfied.

**`OWNER-RUN` tasks:** a scheduled session must **skip** these and take the next
`READY` task instead. If the only remaining work is `OWNER-RUN`, report that and
stop. **There are none outstanding** — T06b was signed off PASS on 2026-08-07.

**Resumable tasks** are marked ⏳. They span several sessions and carry their own
`## Progress` checklist, committed after each stage. They stay `READY` until every
stage is ticked, and partial commits bearing their task ID are expected — not a
sign of a stale board.

---

## Status

### Track A — Finish Phase 1 (gate blockers)

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T01 | [DDA ray-march in `raycast()`](tasks/T01-dda-raymarch.md) | — | `DONE` |
| T02 | [Wall sensing: microtubules + ER/Golgi](tasks/T02-wall-sensing.md) | T01 | `DONE` |
| T03 | [Hazard/reward channels + weight normalization](tasks/T03-steering-normalization.md) | T02 | `DONE` |
| T04 | [Separate god mode from fuzzer; harden fuzzer](tasks/T04-fuzzer-hardening.md) | — | `DONE` |
| T05 | [PixiJS display-object lifecycle fixes](tasks/T05-pixi-lifecycle.md) | — | `DONE` |
| T06a | [Soak measurement — collect gate evidence](tasks/T06a-soak-measurement.md) ⏳ *resumable* | T04, T05 | `DONE` |
| T06b | [Phase 1 gate verdict — **PASS**](tasks/T06b-gate-verdict.md) 👤 *owner-run* | T06a | `DONE` |
| T06c | [**Find and fix the retained-memory leak**](tasks/T06c-heap-leak-hunt.md) | T06a | `DONE` |

> **T06c re-measured before investigating**, per its own Step 0. Re-running
> `soak.py A` at `8762fcf` (T07–T17 landed since the original `30ec41a`
> measurement) over a comparable ~1063s/453-round span shows the heap floor
> now flat (41.7–48.2 MB across 6 windows, no upward trend) versus the
> original's monotonic 44→124 MB climb. Resolved by T07's per-player trace
> cap; no code change was needed. Full before/after tables in the task file's
> `## Findings`.

**Phase 1 gate:** T01–T06a all `DONE`, and T06b's verdict committed as PASS.
T07/T11/T16 intentionally depend on **T06a** (the evidence exists), not on T06b
(the human verdict), so work continues while the report awaits sign-off. If T06b
later returns FAIL, revisit anything that landed in that window.

### Track B — Structural hygiene (cheap, unblocks Phase 3)

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T07 | [Bound trace growth (per-player cap)](tasks/T07-trace-cap.md) | T06a | `DONE` |
| T08 | [Distance-based self-neck immunity](tasks/T08-neck-distance.md) | T07 | `DONE` |
| T09 | [Persist ER geometry across `drawArcs()` redraws](tasks/T09-er-persistence.md) | — | `DONE` |
| T10 | [Dev hotkey alignment + on-screen legend](tasks/T10-dev-hotkeys.md) | T04 | `DONE` |

### Track C — Phase 3 content (generation-gated)

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T11 | [Generation counter infrastructure](tasks/T11-generation-counter.md) | T06a | `DONE` |
| T12 | [Gen 2 — membrane calcification](tasks/T12-gen2-calcification.md) | T11 | `DONE` |
| T13 | [Gen 2 — organelle necrosis (lethal static walls)](tasks/T13-gen2-necrosis.md) | T11 | `DONE` |
| T14 | [Gen 3 — the malignant mass](tasks/T14-gen3-malignant-mass.md) | T11 | `DONE` |
| T15 | [Gen 4 — angiogenesis gravity well](tasks/T15-gen4-angiogenesis.md) | T11 | `DONE` |

### Track D — Phase 4 juice

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T16 | [Camera screenshake utility](tasks/T16-screenshake.md) | T06a | `DONE` |
| T17 | [Particle emitter splash system](tasks/T17-particles.md) | T16 | `DONE` |
| T18 | [Warning-window post-processing filter](tasks/T18-warning-filter.md) | T16 | `DONE` |

### Track E — Phase 5 UX

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T19 | [Quick Play button](tasks/T19-quick-play.md) | T03 | `DONE` |
| T20 | [Control-mapping splash screen](tasks/T20-control-splash.md) | — | `DONE` |

### Track F — Phase 2.2 (renderer-independent)

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T21 | [Extend additive blending on the vector renderer](tasks/T21-additive-blending.md) | — | `DONE` |

### Track G — Architecture (enables Phase 7, speeds up testing)

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T22 | [Separate simulation from rendering](tasks/T22-sim-render-split.md) ⏳ *resumable* | T06a | `DONE` |

> **Phase 1 gate: PASS** — `docs/reports/PHASE1-GATE.md`, signed off 2026-08-07.
> The retention T06c chased was resolved by T07's trace cap: run A re-measured
> flat (41.7–48.2 MB across six windows) over 453 rounds with zero errors.

> **T22 was wrongly left `BLOCKED` until 2026-08-07.** Its only dependency,
> T06a, completed long before — but T06a's definition-of-done checklist named
> only "T07, T11, T16 → READY", because it was written before T22 existed. The
> session that finished T06a flipped exactly the three tasks it was told to.
> **Lesson: when you add a task that depends on an existing one, update that
> task's definition-of-done checklist too**, or the dependency is invisible to
> whoever completes it.

### Track H — Phase 6: Mobile

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T23 | [Viewport, touch input, orientation](tasks/T23-mobile-viewport-touch.md) | — | `DONE` |
| T24 | [Touch-friendly menu and HUD](tasks/T24-touch-ui.md) | T23 | `DONE` |
| T25 | [Incremental trace rendering](tasks/T25-trace-render-perf.md) | T24 | `DONE` |
| T26 | [Graphics quality tiers](tasks/T26-quality-tier.md) | T25 | `DONE` |
| T27 | [Installable PWA (offline, home screen)](tasks/T27-pwa.md) | T26 | `DONE` |

### Track I — Phase 7: Multiplayer

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T28 | [Fixed-timestep simulation](tasks/T28-fixed-timestep.md) | T22 | `READY` |
| T29 | [Network transport and lobby](tasks/T29-net-transport-lobby.md) | T28 | `BLOCKED` |
| T30 | [Host-authoritative state sync](tasks/T30-host-authoritative-sync.md) | T29 | `BLOCKED` |
| T31 | [Client prediction and interpolation](tasks/T31-client-prediction.md) | T30 | `BLOCKED` |
| T32 | [Network resilience and disconnects](tasks/T32-net-resilience.md) | T31 | `BLOCKED` |

### Track J — Playtest fixes (owner session 2026-08-07)

**Take these before Track G/I.** They are defects in shipped behaviour; the
sim/render split can wait behind them.

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T33 | [Trace invisible outside Cell A (bridge/Cell B)](tasks/T33-trace-rt-bounds.md) ⚠️ *first* | — | `DONE` |
| T34 | [Split-screen choppy and stuttering](tasks/T34-splitscreen-stutter.md) | — | `DONE` |
| T35 | [Dev hotkeys: drop `[`/`]`, legend must match](tasks/T35-dev-hotkeys-legend.md) | — | `DONE` |
| T36 | [Target mode: legend wrong, attack does almost nothing](tasks/T36-targetmode-legend-and-attack.md) | — | `DONE` |
| T37 | [Calcification: double membrane, organelle bounce](tasks/T37-calcification-visuals.md) | — | `DONE` |
| T40 | [Make pause discoverable](tasks/T40-pause-discoverability.md) | — | `DONE` |
| T43 | [Blue vesicle's Golgi-pass effect does nothing](tasks/T43-blue-vesicle-golgi-pass.md) | — | `DONE` |
| T44 | [Split-screen RenderTexture quality/cost](tasks/T44-splitscreen-quality-and-cost.md) | — | `DONE` |
| T45 | [Start menu never fully hides on mobile](tasks/T45-mobile-menu-not-hidden.md) | — | `DONE` |
| T46 | [Opening Help does not pause the round](tasks/T46-help-does-not-pause.md) | T41 | `DONE` |
| T47 | [Tubulin motif invisible in shared camera (zoom never reaches the LOD gate)](tasks/T47-dimer-lod-never-reached.md) | T42 | `DONE` |
| T48 | [Aggregate drawn in a rectangular frame; survives outside the membrane](tasks/T48-aggregate-grid-outline-and-containment.md) | T39 | `DONE` |
| T49 | [Membrane protrusions and fill stay on the round-start ellipse](tasks/T49-membrane-furniture-follows-shrink.md) | T12, T37 | `DONE` |
| T50 | [Red mode kills you on necrotic organelles it promised to break](tasks/T50-red-mode-necrosis-inconsistent.md) | T38 | `DONE` |
| T58 | [Red vesicle in attack mode instantly kills the opponent](tasks/T58-red-vesicle-instakills-opponent.md) | T08, T36 | `DONE` |

### Track K — Playtest design & features

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T38 | [Necrosis: fuse, shed debris, break apart in red mode](tasks/T38-make-necrosis-matter.md) | T36, T37 | `DONE` |
| T39 | [Replace the "tumour" with a protein aggregate; grow faster](tasks/T39-aggregate-not-tumour.md) | — | `DONE` |
| T41 | [How-to-play tutorial](tasks/T41-tutorial.md) | T36, T40 | `DONE` |
| T42 | [Trace as tubulin-dimer microtubule](tasks/T42-tubulin-trace.md) | T33 | `DONE` |
| T51 | [Give the player a way to fight the shrinking membrane (ATP)](tasks/T51-slow-the-calcification.md) | T12 | `DONE` |
| T52 | [Gen 4: the nucleus feeds, and the player starves it](tasks/T52-gen4-nucleus-feeding.md) | T15 | `DONE` |
| T56 | [Make the trace read as a microtubule, and animate it assembling](tasks/T56-microtubule-lattice-and-assembly.md) | T42, T47 | `DONE` |
| T57 | [When the nucleus is full: the cell turns on the microtubule](tasks/T57-transformed-nucleus.md) | T52 | `DONE` |

> **Phase 9 — after Gen 4.** Scoped in
> [`PHASE9-LATE-GAME-ARC.md`](PHASE9-LATE-GAME-ARC.md): Gen 5+ currently exists
> and is **empty** (the largest `genAtLeast()` gate in the codebase is 4, and
> `massGrowInterval()` floors from Gen 4 on), so surviving Gen 4 today earns a
> counter increment and nothing else. The note recommends Gen 5 = immune
> response (reuses T57's chasing entity, and introduces baiting) and Gen 6 =
> escape, which would be the game's first win condition. **Deliberately no task
> files yet** — none of it should be written before T52/T57 have been played.

### Track L — Phase 8: Scoring, statistics and upgrades

Scoped in [`PHASE8-META-PROGRESSION.md`](PHASE8-META-PROGRESSION.md). This is the
game's first state that survives a round, so it goes after Track J's defects and
after T22 — build and play each layer before adding the next.

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T53 | [Run stats and a score](tasks/T53-run-stats-and-score.md) | — | `READY` |
| T54 | [Persistent high-score table](tasks/T54-high-score-table.md) | T53 | `BLOCKED` |
| T55 | [Microtubule upgrades](tasks/T55-microtubule-upgrades.md) | T54 | `BLOCKED` |

### Parked

| ID | Task | Reason |
|----|------|--------|
| P01 | Phase 2.1 — sprite/asset pipeline | Owner decision: the vector→image substitution did not look right. Needs a different approach before it is re-planned. See [`tasks/P01-asset-pipeline-parked.md`](tasks/P01-asset-pipeline-parked.md). **Phase 2.2 is not parked** — it is T21 above, and it does not depend on the asset swap. |

---

## Dependency graph

```
T01 ──► T02 ──► T03 ───────────────► T19
T04 ──┬───────► T06a ──┬─► T07 ──► T08
T05 ──┘         │      ├─► T11 ──┬─► T12
T04 ──► T10     │      │         ├─► T13
                │      │         ├─► T14
T09 (indep.)    │      │         └─► T15
T20 (indep.)    │      └─► T16 ──┬─► T17
T21 (indep.)    │                └─► T18
                ├─► T06b  👤 owner verdict — gates nothing downstream
                └─► T22 ──► T28 ──► T29 ──► T30 ──► T31 ──► T32   (Phase 7)

T23 ──► T24 ──► T25 ──► T26 ──► T27                              (Phase 6, independent)
```

Five entry points are independent and can be picked up at any time if the head of
a track is blocked: **T09**, **T20**, **T21**, **T23** (which opens all of
Phase 6), and — before T04 lands — **T05**.

**Phase 6 (mobile) depends on nothing.** It can run in parallel with Phase 1–5
work at any time. **Phase 7 (multiplayer) depends on T22**, the sim/render split,
which is why T22 is worth doing before Phase 3 content piles up on top of the
fused architecture.

---

## Current state of the code — reference

Established by reading `260703_Cellsnake.html` at commit `4bf057f`. Anchor by
function name, not by line number.

**Present and working**
- `SpatialGrid` class + `rebuildSpatialGrid()` — traces, organelles, vesicles,
  virus particles, rebuilt once per frame at the top of `gameLoop`.
- Swept collision helpers `ptSegDistSq`, `segsCross`, `segSegDistSq`.
- `checkCollision()` / `checkArcCollision()` — swept, correct, frame-aware.
- 3-ray bot (`updateBotAI`, `raycast`, `getRayWeight`), ±0.5 rad, 350px range.
- Mitosis engine, infection/virus event, vesicle economy, split-screen camera.

**Known gaps (these are the tasks)**
- `raycast()` samples at a fixed 12px step and allocates a `Set` + array per
  step via `queryRange` — ~90 allocations per bot per frame.
- `raycast()` is blind to `mitosis.microtubules` and to `centralHitboxes`
  (ER/Golgi), both of which are lethal in the physics path.
- `getRayWeight()` hazard term reaches ≈ −612,500 while the vesicle reward is
  +2,000 and the mitosis pull ≈ ±470 — rewards are ~1300× outweighed.
- `devMode` disables all death checks *and* gates the fuzzer, so the fuzzer
  cannot find collision bugs.
- `generateMap()` and the organelle reset use `removeChildren()` without
  destroying the children — display objects leak on every `startRound()`.
- Traces grow unbounded (~3,600 points/player/minute); the grid rebuild is
  linear in total trace length every frame.
- `drawArcs()` re-randomizes the ER layout on every call, so the ER teleports
  whenever any arc shatters (the Golgi has this fixed via `window.golgiData`;
  the ER does not).
- Additive blending covers `trailGlow`, `trailCore` and the Golgi cisternae only;
  organelles, vesicles, the virus and the ER are still normally blended. A global
  `AdvancedBloomFilter` is active on `world` (`pixi-filters@5.2.1` is loaded).
- No `activeCell.generation` field exists — all of Phase 3 needs it.
- Dev hotkeys are `` ` ``/`~`/`½` (god mode) and `Tab` (+15s); the roadmap
  specifies `\` and `]`.
