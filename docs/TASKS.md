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
> **Everything through T58, Track L and Phase 7 has landed.**
>
> ### ⚠️ Owner playtest 2026-08-11 — take these in this order
>
> **T60 → T59 → T61 → T62.**
>
> - **T60** (first): the sim unfreezes ~2.4–4.7 game-seconds *before* the event
>   camera stops moving, so the zoom changes 4–5× while the player is already
>   steering — and because `updateCamera()`'s lerps are still per-frame after
>   T28, it behaves differently on every device. Adds the owner's 3-2-1
>   countdown. Measured both ways in the task file.
> - **T59**: "Shed the Tail" is keyboard-only, so it can be bought on a phone
>   and never used.
> - **T61**: HUD/menu restructure — the nucleus meter is drawn over the
>   scoreboard, the control legend is printed twice, the post-round result is
>   buried under the setup UI, and the phone menu is cut off with no scroll cue.
> - **T62**: art pass, resumable, **one section per session**.
>
> Phase 9 (`PHASE9-LATE-GAME-ARC.md`) is scoped but still deliberately has no
> task files.
>
> **T60 landed 2026-08-13** — every `updateCamera()` lerp is now time-based
> (`camLerpFactor(k, deltaSec)`, exactly reproducing the old per-frame-at-60fps
> feel when `deltaSec` is `1/60`) and driven by the *total* game-time simulated
> since the last render (not one step's `deltaSec`), fixing the frame-rate
> dependence. The mitosis reveal is now a `hold -> zoomback -> countdown ->
> play` phase machine gated on the camera actually reaching its target
> (`cameraAtTarget`, with a `MITOSIS_REVEAL_SETTLE_TIMEOUT` safety net for
> headless runs that never call `updateCamera()` at all), not a fixed 5.0s
> stopwatch; the same shared `REVEAL_COUNTDOWN=3.0` 3-2-1 countdown was added
> to the infection breach and T57's nucleus transformation too (folding its
> separate `NUCLEUS_TRANSFORM_GRACE` buffer in, per the task's own
> instruction). Mitosis reveal framing now fits the two cells' true bounding
> box instead of a fixed square, fixing the letterboxing for the
> matched-orientation case. Verified: zoom change after control returns is
> 0.0 (640x480) / 0.04 residual-from-live-movement (1280x1024) versus the old
> 4-5x; both viewports reach control-return at the identical 8.217 game-seconds
> (frame/viewport independence); all three events' countdowns measured and
> screenshotted; 5 forced mitosis events with 3 bots showed zero deaths during
> any freeze/countdown window; split-screen's fixed zoom confirmed untouched;
> a forced headless mitosis event resolved via the safety timeout instead of
> deadlocking. `sw.js` `CACHE_NAME` bumped v38→v39; `dist/` rebuilt. See
> `docs/tasks/T60-event-camera-and-countdown.md` Findings for full numbers.
>
> **T59 landed 2026-08-13** — a touch-only Shed the Tail button (`#shedTailBtn`,
> bottom-left corner, mirrors T23's `#touchToggleBtn` in the opposite corner)
> is shown only when `isTouchDevice && players[0].upgrades.shedTail`, driven
> by a new draw-only `updateShedTailButtonHUD()` that mirrors T52's
> `updateNucleusFeedHUD()` show/hide idiom exactly; tapping it calls the same
> `deleteOldestTrace()` the existing 'x' key already uses, with a live
> countdown replacing the scissors glyph while on `SHED_TAIL_COOLDOWN`. The
> shop description is no longer a fixed "Press X" string — `UPGRADES.shedTail.desc`
> is now a function of `isTouchDevice`. Verified: atomic (same-tick)
> before/after trace counts prove the ~30% cut (25→18 live, 143→101 after a
> forced cooldown expiry) and prove the immediate second tap is a no-op
> (18→18); `document.elementFromPoint()` swept across both 390x844 and
> 844x390 hits the canvas everywhere except the two 56x56 button footprints
> (no steering swallowed, unlike T45's old `#ui-trigger` strip); a synthetic
> held touch `pointerdown` elsewhere on the canvas still sets `keys.ArrowLeft`
> for the hold's duration; desktop (`isTouchDevice=false`) keeps the button at
> `display:none` throughout and the 'x' key still works unchanged; console
> clean over both `http://` and `file://` (`dist/`); a real 20.2s round played
> normally. No hazard changed (`checkCollision`/`checkArcCollision`/`raycast`/
> `rebuildSpatialGrid` don't appear in the diff), so §4.1/§7.6 don't apply,
> same reasoning T54/T55 recorded. `sw.js` `CACHE_NAME` bumped v39→v40; `dist/`
> rebuilt. See `docs/tasks/T59-shed-tail-unreachable-on-touch.md` Findings for
> full numbers.
>
> **T61 landed 2026-08-13** — one ordered top-centre HUD stack (`#liveHud`:
> `#scoreboard` + `#nucleusFeedBar`, always visible independent of `#ui`'s own
> show/hide) replaces the two independently-positioned elements that used to
> land on top of each other at Gen 4; the boost-target legend is now stated
> once (attached to the control cards) instead of twice; round-over shows the
> stats card + a prominent Play Again first, with setup collapsed behind a
> `<details>` disclosure; a scroll-fade plus a short-landscape media query fix
> the phone menu (primary action now reachable with 0 scrolling at 844×390,
> was cut in half); Help/Scores/Shop/Online each get a distinct icon + accent
> colour; P3/P4 control cards are omitted (not dimmed) when not configured;
> the redundant in-panel × was deleted (`#pauseMenuBtn` already does the same
> job); the stray pre-round "Survival Time: 0.0s" is gone. Fixing item 1
> surfaced two knock-on bugs from moving `#scoreboard` out of `#ui` (a 48px
> sliver of `#ui` left visible when nominally hidden, and `#liveHud` bleeding
> through the four modal overlays' scrim) — both caught before commit via
> direct `getBoundingClientRect()`/screenshot checks, not by eye, and fixed
> with a shared `--ui-top-offset` custom property and a
> `MutationObserver`-driven `updateLiveHudVisibility()` respectively. No
> hazard touched — `checkCollision`/`checkArcCollision`/`raycast`/
> `rebuildSpatialGrid` don't appear in the diff (confirmed by grep) — but the
> §7.6 sweep was still run for real: membrane death fires correctly at all 3
> speeds with the new round-over UI rendering clean, and a real 30.2s round (1
> player + 3 bots) played normally with the pause menu and control splash
> exercised mid-round. Verified over both `http://` and `file://`, including
> the rebuilt standalone `dist/Cellular_Zatacka.html`. `sw.js` `CACHE_NAME`
> bumped v40→v41; `dist/` rebuilt. See
> `docs/tasks/T61-hud-and-menu-restructure.md` Findings for full numbers and
> screenshots.
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
>
> **T53 landed 2026-08-11** — per-player `p.stats` (vesicles by type, cluster/
> mass breaks, mitosis events, distance, max generation reached), a
> `scoreRun()` with named weights that deliberately let generations dominate
> (worked examples: timid Gen 1 580, aggressive Gen 2 2086, long Gen 3 3795),
> and an end-of-round card extending the existing `#ui`/`#scoreboard` game-over
> spot (readable and reachable at 390x844/844x390/1280x800, restart still works
> both by keyboard and click with the card up). Bots get the same stats object,
> no special-casing. Distance proven frame-rate independent (1800/1800/1800.75px
> across dt=1/20, 1/60, 1/120 for the same 20 game-seconds) and speed-proportional
> (1800px at Normal vs 4200px at Very Fast). `worldChildren` flat (16) across 20
> scripted restarts; regression sweep (§7.6) passed at all 3 speeds via direct
> `checkCollision()` calls. `sw.js` `CACHE_NAME` bumped v30→v31; `dist/` rebuilt.
> See `docs/tasks/T53-run-stats-and-score.md` Findings for full numbers.
>
> **T54 landed 2026-08-11** — human runs (bots excluded) now persist to a
> versioned, capped (`HISTORY_MAX=50`) `localStorage` key, with lifetime
> totals tracked independently of the capped run list so they stay true
> lifetime figures; a new "Scores" panel (reusing T41's help-overlay
> structure and pause/outside-click/Escape-P wiring exactly) shows the top 10
> runs by score (mode-labelled, e.g. `1h3ai`) plus the totals, with a
> confirm-gated Clear History button. The end-of-round card now calls out
> "New Best!" when a run beats the mode's prior best. All three storage
> failure modes (`setItem` throwing, corrupt JSON, wrong schema version) proven
> survivable by direct fault injection; the new-best callout proven to fire
> only on an actual new best (not on a lower score, and correctly on a mode's
> first-ever run); `HISTORY_MAX` proven to hold at exactly 50 runs (9,252
> bytes stored at the cap); persistence proven across a real page reload and
> under `file://` (offline); panel screenshotted legible at 390x844, 844x390
> and 1280x800. No hazard was added and `checkCollision()`/`checkArcCollision()`/
> `raycast()`/`rebuildSpatialGrid()` are untouched, so §7.6's regression sweep
> doesn't apply here. `sw.js` `CACHE_NAME` bumped v31→v32; `dist/` rebuilt. See
> `docs/tasks/T54-high-score-table.md` Findings for full numbers.
>
> **T55 landed 2026-08-11 — Track L (Phase 8) is now fully done.** Three
> upgrades, bought with points banked from every recorded run's score (`HS_VERSION`
> 1→2, migrated in place): Wider Pickup Radius (+12px vesicle/ATP collection
> distance), Shed the Tail ('x' key, 30s cooldown, cuts the oldest 30% of your
> own trace via the existing `deleteOldestTrace()`), and Choice of Spawn (pick
> which of the 4 starting slots you begin at, persisted alongside the save).
> Two of the task's five suggested examples ("second boost slot", "faster
> target-mode switching") don't map onto anything the codebase actually
> restricts today and were skipped rather than faked — see Findings. Resolved
> once per player at round start (`resolvePlayerUpgrades()` → `p.upgrades`),
> bots always get the human's exact loadout, and everything is guarded off
> whenever `currentMode > 1` (local multiplayer) — confirmed empty upgrades
> and default spawn for a 2-human round even with all 3 owned. No hazard
> constant touched (`TRACE_HITBOX`/`EFFECT_DURATION`/the three hit-cooldowns
> read back identical under a full loadout; `checkCollision`/`checkArcCollision`/
> `raycast`/`rebuildSpatialGrid` don't appear in the diff at all). Purchase is
> atomic against induced storage failure (write-first, verified both ways);
> persistence survives a real reload; a real v1 (T54-era) payload migrates
> cleanly to v2. Win-rate check: 10 headless Gen-2 4-player rounds with every
> player (human slot piloted by the same AI as the bots, for lack of a
> scriptable human) holding the identical full loadout — human slot won 1/10,
> nowhere near making anyone unbeatable. Shop panel (new overlay, mirrors
> T41/T54's structure exactly) screenshotted legible at 390×844, 844×390 and
> 1280×800. `sw.js` `CACHE_NAME` bumped v32→v33; `dist/` rebuilt. Two
> incidental findings filed to `docs/BACKLOG.md` (raycast()'s reward-sensing
> radius doesn't reflect the pickup upgrade; a suspicious starting-slot skew
> in the base 4-player win distribution). See
> `docs/tasks/T55-microtubule-upgrades.md` Findings for full numbers.
>
> **Track L (Phase 8) is fully done. Next up: Phase 7, starting with T28
> (fixed-timestep simulation), already `READY`.**
>
> **T28 landed 2026-08-11** — `gameLoop()` now drives `stepSimulation()`
> through a fixed-timestep accumulator (`FIXED_DT=1/60`, clamped to 0.25s per
> real frame, capped at `MAX_STEPS_PER_FRAME=5` against the spiral of death),
> so simulation steps — and everything rolled per-step — no longer run at a
> fraction of the rate on a slow display. Gap chance/length converted from
> per-frame counts to world-distance triggers (`GAP_DISTANCE_MEAN=187.5`,
> `GAP_LENGTH_DIST=18`, derived from the old `GAP_CHANCE`/`GAP_LENGTH` at
> 60fps and Normal speed — see the file's own T28 comment for the arithmetic),
> so gap spacing is now independent of speed setting as well as frame rate;
> vesicle spawn converted to an explicit `VESICLE_SPAWN_PER_SEC=0.48` rate
> (numerically identical to the old per-frame roll at 60fps, `0.008 * 60`).
> Verified: manually pacing `gameLoop()` at 15/30/60/120fps for 60 real
> seconds each produced an *identical* `survivalTime` (60.08s) at every rate;
> vesicle-spawn and gap-count means converged to within ~2-3% between the
> 15fps and 120fps extremes over 6-trial samples (28.83 vs 29.5 vesicles,
> matching the ~28.8 analytical expectation; 109.3 vs 106 total trace
> segments); gap length in world units went from the old 18/30/42px spread
> (Normal/Fast/Very Fast, proportional to speed) to 18/20/21px (quantization
> noise only); a forced single-frame 30-second stall advanced `survivalTime`
> by only 0.084s (the `MAX_STEPS_PER_FRAME` cap) with a 7.5px player move, not
> a 30s fast-forward or a teleport, and normal pacing resumed cleanly right
> after; pause/resume freezes and resumes exactly, no burst. Render
> interpolation between steps deliberately deferred, per the task's own
> design note — see `docs/BACKLOG.md`. `sw.js` `CACHE_NAME` bumped v33→v34;
> `dist/` rebuilt. See `docs/tasks/T28-fixed-timestep.md` Findings.
>
> **T29 (network transport and lobby) is now `READY`** — its only dependency,
> T28, is done.
>
> **T29 landed 2026-08-11** — an Online (beta) panel (mirrors T41/T54/T55's
> overlay structure) lets a host create a 4-6-character room code (no
> `0/O/1/I/L`) and up to 3 clients join it over a small WebSocket relay
> (`tools/relay_server.js`, new -- `npm install` once, `node relay_server.js
> [port]`), not WebRTC DataChannels -- the task's own "if signalling proves
> painful" fallback, chosen because this sandbox has no reachable STUN/TURN
> or signalling broker to verify against and no library to vendor without a
> CDN (see Findings for the full reasoning). A one-place versioned message
> envelope (`NET_PROTOCOL_VERSION`, mirrored in both files) covers
> create/join/lobby/start/input/state/ping/pong/bye; clients sample the
> existing `keys` object at 30Hz with sequence numbers once the host starts
> the (still gameplay-free) transport demo, the host sends a 10Hz stub state
> heartbeat, and both sides ping at 1Hz for a displayed RTT. Nothing in
> `startRound()`/`stepSimulation()`/`gameLoop()`/`checkCollision()`/
> `raycast()` was touched -- confirmed by grepping the diff. Verified with
> real Playwright-driven browsers: 2 peers (room code, version-mismatch
> refusal, RTT display, client-leave and host-leave detection, all console
> clean) and 4 peers in one room (all listed, all exchanging input, `?relay=`
> override proven) against `tools/relay_server.js`; single-player proven completely unaffected (zero
> WebSocket connections opened, `netState` untouched, console clean) over
> both `http://` and `file://`; one real bug caught in verification
> (`netHostStart()` read config globals that are undefined before
> `updateUI()` has ever run -- fixed to read the DOM selects directly, same
> rule `tools/verify_harness.py`'s own "TRAP 3" already documents). `sw.js`
> `CACHE_NAME` bumped v34→v35; `dist/` rebuilt. WebRTC migration noted to
> `docs/BACKLOG.md` as explicit follow-up work, out of scope here. See
> `docs/tasks/T29-net-transport-lobby.md` Findings for full numbers.
>
> **T30 (host-authoritative state sync) is now `READY`** — its only
> dependency, T29, is done.
>
> **T30 landed 2026-08-12** — the host now runs the only `stepSimulation()`;
> clients skip it entirely and just `renderFrame()` from network snapshots
> written straight into the existing `players[]`/`organelles[]`/`vesicles[]`
> module state, so `updateCamera()`/`drawPlayerBars()`/`drawTraces()`/every
> other draw function needed zero changes. Player state broadcasts at 20Hz,
> organelles/vesicles/membrane radii at 5Hz, both as positional arrays with
> rounded numbers (an early keyed-object wire format measured ~12KB/s for a
> 4-player match; switching to arrays + dropping the redundant `color` field
> brought that to ~2KB/s each direction, inside the design note's "low
> single-digit KB/s"). Traces are never sent -- reconstructed client-side from
> head position + `isGap` using the same segment-boundary rule
> `updatePlayers()` itself uses. Verified with real Playwright/WebSocket-relay
> peers: 2-player and 4-player (host+2 clients+1 bot) matches play with
> matching positions/traces/organelles; gaps appear on remote screens; 10/10
> forced deaths agreed between host and client; out-of-order and 20%-dropped
> messages proven harmless (self-healing full-list/staleness design); a
> `window.checkCollision` call-counter proved 0 calls on either client across
> a full trial (387-420 on the host); offline single/local-multiplayer and
> `file://` both regression-clean, plus the full §7.6 sweep (membrane/
> trace/organelle death, near-miss survival) at all 3 speeds --
> `checkCollision`/`raycast`/`checkArcCollision`/`rebuildSpatialGrid` are
> untouched by this diff. **Scope note:** ER/Golgi wall geometry, Gen 2+
> hazard systems (necrosis, the malignant mass, ATP, nucleus chasers), and
> full mitosis/infection state are *not* synced -- the task's own design
> table predates most of that content; every verification round stayed
> within Gen 1 and under `MITOSIS_INTERVAL`/the infection warning timer so
> the gap doesn't invalidate the results. Filed to `docs/BACKLOG.md` with the
> concrete mechanism each would need (a seeded-PRNG pass for ER/Golgi is the
> likely fix, using the `seed` field T29 already carries but this task never
> consumed). See `docs/tasks/T30-host-authoritative-sync.md` Findings for
> full numbers.
>
> **T31 (client prediction and interpolation) is now `READY`** — its only
> dependency, T30, is done.
>
> **T31 landed 2026-08-12** — remote players now render ~100ms in the past,
> linearly interpolated between buffered snapshots (`netInterpolateRemotePlayers()`,
> shortest-arc angle blend); the local player's own head is predicted every
> rendered frame from live `keys` (`netPredictLocalPlayer()`) and reconciled
> by rewind-and-replay against the host's per-player input-ack seq
> (`netReconcileLocalPlayer()`, a 12th element added to `netBuildStateMessage()`'s
> per-player array). Both the host and the network client now move a human
> head through exactly one function, `computeMovementStep()` -- extracting it
> surfaced a real bug (a stale `actualSpeed` reference 40 lines below the old
> inline calc, only caught by actually running a round in a browser, not by
> `node --check`), fixed by computing the equivalent `Math.hypot()` distance
> instead. Verified with real Playwright peers over `tools/relay_server.js`:
> prediction responds within the next rendered frame (no network round-trip);
> remote motion sampled at ~60Hz stayed in small continuous increments (mean
> 7.7-7.9px, max 15-16px) rather than 50ms stair-steps; reconciliation jumps
> stayed bounded (max ~15px) under both a clean local link and an injected
> 200ms-latency/5%-loss link, with no growth or oscillation; 10/10 forced-death
> trials under 200ms delay showed the client's local-player `alive` flag
> transition cleanly `true→false` and never flip back (no predicted deaths, no
> un-dying); full offline §7.6 regression sweep passed at all 3 speeds.
> `sw.js` `CACHE_NAME` bumped v36→v37; `dist/` rebuilt. See
> `docs/tasks/T31-client-prediction.md` Findings for full numbers.
>
> **T32 (network resilience and disconnects) is now `READY`** — its only
> dependency, T31, is done.
>
> **T32 landed 2026-08-12 — Track I (Phase 7: multiplayer) is now fully done.**
> Staged `lagging`(>1s)/`dropped`(>5s)/`gone`(>15s) silence classification
> reuses the existing ping/pong + gameplay traffic as its heartbeat (no new
> message type); a client crossing `dropped` is handed to the bot AI
> (`p.isBot=true`, T03's bot is competent) and handed back on recovery or
> rejoin. A departed non-host peer can rejoin its exact slot within 15s via a
> persistent per-browser `cid` the relay tracks (`tools/relay_server.js`'s new
> `room.departed`/`REJOIN_WINDOW_MS`), restoring a downsampled trace snapshot
> (every 8th point) so the rejoined screen looks right -- measured at 6364
> bytes for a synthetic 4000-point trace. Host disconnect (or a hung host that
> never sends `hostLeft`, caught by the same heartbeat) ends the match
> honestly for every client: final standings, forced-open panel, back to the
> room picker, never a frozen canvas -- stated in the lobby UI before a match
> starts too. `visibilitychange` tells the host "backgrounded" (not an
> alarming drop) and asks for a fresh snapshot on return. Two real bugs only
> caught by testing with actual Playwright peers (not synthetic delays): a
> straggler message in flight when a socket closed could silently undo a
> confirmed drop's bot handoff (fixed with a `confirmedGone` latch cleared
> only by an explicit rejoin); and the close handler never nulled `netState.ws`,
> so reopening the panel after an involuntary drop showed a dead-end screen
> with no way back in. Verified with real 2- and 4-peer Playwright rounds over
> `tools/relay_server.js`: client-drop, host-drop, a 3.5s silent-but-connected
> blip that recovers without ever dropping, a real 8s socket-close-then-rejoin
> (item 4's own number), and all 3 clients in a 4-peer room closing
> simultaneously leaving the host running with zero console errors. Host
> migration stays out of scope (design's own §3; already in
> `docs/BACKLOG.md`). `checkCollision`/`checkArcCollision`/`raycast`/
> `rebuildSpatialGrid` untouched -- §7.6 doesn't apply. `sw.js` `CACHE_NAME`
> bumped v37→v38; `dist/` rebuilt. See `docs/tasks/T32-net-resilience.md`
> Findings for full numbers.
>
> **Nothing depends on T32** -- it was the last task in Track I's dependency
> chain. No other task's status changes as a result.

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
| T28 | [Fixed-timestep simulation](tasks/T28-fixed-timestep.md) | T22 | `DONE` |
| T29 | [Network transport and lobby](tasks/T29-net-transport-lobby.md) | T28 | `DONE` |
| T30 | [Host-authoritative state sync](tasks/T30-host-authoritative-sync.md) | T29 | `DONE` |
| T31 | [Client prediction and interpolation](tasks/T31-client-prediction.md) | T30 | `DONE` |
| T32 | [Network resilience and disconnects](tasks/T32-net-resilience.md) | T31 | `DONE` |

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
| T59 | ["Shed the Tail" unreachable on touch](tasks/T59-shed-tail-unreachable-on-touch.md) | T55 | `DONE` |
| T60 | [Play resumes while the camera is still moving](tasks/T60-event-camera-and-countdown.md) ⚠️ *first* | T28, T47 | `DONE` |
| T61 | [HUD collides with itself; the menu is a wall](tasks/T61-hud-and-menu-restructure.md) | T53, T54, T55 | `DONE` |
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
| T62 | [Art pass: depth, scale and the bridge](tasks/T62-art-pass-depth-and-scale.md) ⏳ *resumable, one section per session* | T60, T61 | `READY` |

> **T62 Section 1 (scale collapse) landed 2026-08-14** — small, low-alpha
> "filler" cytosol blobs (`spawnCytosolFiller()`, tier-driven count: low 0 /
> medium 400 / high 600) now fill the gaps between the existing sparse large
> blobs, reusing the same `cytosolParticles` array and per-frame drift/pulse
> loop so no new per-frame code was added. Cost measured directly:
> 0.075ms/frame at 636 particles (filler off) vs 0.109ms/frame at 1095
> (filler on). `worldChildren` flat (16) across a 300-game-second headless
> run; low tier confirmed to drop the detail entirely (0 extra particles).
> No hazard function touched. `sw.js` `CACHE_NAME` bumped v41→v42; `dist/`
> rebuilt.
>
> **T62 Section 2 (membrane low-zoom treatment) landed 2026-08-14** —
> `drawCalcification()` now boosts every ring's stroke width by
> `zoomBoost = Math.max(1, 1 / world.scale.x)` (T52's existing nucleus-well
> pattern) so the membrane no longer thins to one line at the ~0.5-0.6 zoom
> the game is actually played at, plus a new tier-gated soft inner glow
> (`QUALITY_TIERS[tier].membraneGlowSteps`: low 0/medium 2/high 3) falling
> from the ring into the cytosol. Cost measured at 0.0044-0.0058ms/call across
> tiers (negligible against the 16.6ms frame budget); `worldChildren` flat
> over a 300-game-second headless run; a real 30.2s round and an offline
> `file://` load of the rebuilt `dist/` both console-clean; no hazard function
> in the diff. `sw.js` `CACHE_NAME` bumped v42-v43; `dist/` rebuilt. Cell B's
> matching mitosis-time membrane bake has the same issue but is out of scope
> here -- filed to `docs/BACKLOG.md`. Sections 3-6 remain — see
> `docs/tasks/T62-art-pass-depth-and-scale.md` `## Progress`/`## Findings`.
>
> **T62 Section 3 (mitosis bridge as a curve) landed 2026-08-14** — root cause
> was that `isOutsideCell()`'s real bridge boundary already narrows from each
> cell's own ellipse down to the corridor's flat half-width, but the old
> straight wall started at a fixed `radiusX - 10` offset *past* that true
> crossing point, creating a ~200px visual jump against the still-fully-drawn
> membrane ring. `drawMitosisVisuals()` now starts the corridor exactly at the
> true ellipse/half-width crossing point (computed fresh each frame from
> `activeCell.radiusX/radiusY`/`mitosis.currentWidth`, the same values the real
> hazard already uses) plus a small `quadraticCurveTo` flare at each end,
> producing a continuous hourglass neck instead of a rectangle butted against
> two circles -- purely cosmetic, `isOutsideCell()`/`checkCollision()`/
> `checkArcCollision()`/`raycast()`/`rebuildSpatialGrid()` all absent from the
> diff. Cost 0.0202ms/call before vs. 0.0254ms/call after (negligible);
> `worldChildren` flat over a 300-game-second headless run; before/after
> screenshots at zoom 0.55 for a forced horizontal event confirm the jump is
> gone, plus a vertical-direction sanity screenshot and a `currentWidth` sweep
> (600 down to 0) with no throw/NaN. `sw.js` `CACHE_NAME` bumped v43-v44;
> `dist/` rebuilt. One pre-existing, already-backlogged issue (mitosis snap's
> kill check gated on `devMode` not `godMode`) surfaced incidentally, not
> re-filed.
>
> **T62 Section 4 (depth: parallax + edge falloff) landed 2026-08-14** —
> `cytosolContainer` (the shared background-blob container) now gets a
> rendering-only parallax offset, recomputed fresh every frame from the
> camera's current focus point (never accumulated, same discipline
> AGENT_CONDUCT 4.5 requires of `world.x/y`), so the background blobs read as
> a layer further back than the foreground; verified algebraically exact
> against the formula. `drawCalcification()` gains an outward falloff mirroring
> section 2's inward glow (same `glowSteps`/`zoomBoost`/tier gate) — a first
> near-black attempt proved indistinguishable from `backgroundColor` and was
> screenshotted, rejected, and replaced with the membrane's own outer-glow blue
> bleeding outward with decreasing alpha, confirmed clearly visible in a
> before/after at the true playing zoom (0.55) and confirmed dropped at low
> tier. Cost unchanged within measurement noise (`drawCalcification()`
> 0.0099→0.0111ms/call, `updateAndDrawBackgroundElements()`
> 0.1365→0.1231ms/call); `worldChildren` flat over a 300-game-second headless
> run; a real 13.9s round (1 human + 3 bots) played and ended normally;
> offline `file://` load of the rebuilt `dist/` console-clean. No hazard
> function or `activeCell.radiusX/radiusY` write in the diff. `sw.js`
> `CACHE_NAME` bumped v44→v45; `dist/` rebuilt. Sections 5-6 remain — see
> `docs/tasks/T62-art-pass-depth-and-scale.md` `## Progress`/`## Findings`.
>
> **T62 Section 5 (hazard colour language table) landed 2026-08-14** — wrote
> the two-family rule (always-lethal = saturated/alive, breakable-in-attack-mode
> = desaturated/mineral) as a table covering every hazard's draw code, which
> surfaced one real violation: nucleus chasers (breakable, T57) reused the live
> lysosome organelle's exact colours (`0xff4757`/`0xff6b81`, also the game's
> established "lethal red" for the virus and the mitosis death-ring), so a
> player couldn't tell a chaser from a lysosome by colour even though only one
> of them can be broken. Recoloured the chaser (`drawNucleusChasers()` and its
> `destroyNucleusChaser()` break-particle burst) to a desaturated dusty rose
> (`0xad5a72`/`0xc97e93`, ~34-41% as saturated as the original by HSL) sharing
> the necrotic-grey/aggregate-amber register while staying its own distinct
> hue. Verified with close-up and true-playing-zoom (0.55) screenshots showing
> the chaser and lysosome no longer colour-identical; `drawNucleusChasers()`
> cost 0.0127ms/call (a constant swap, no new draw calls); `worldChildren`
> flat at 16; a real 15.1s round and an offline `file://` `dist/` load both
> console-clean. No hazard function in the diff. A known exception (necrotic
> debris' grey-blue reads closer to the breakable family despite being
> always-lethal) was left alone and filed to `docs/BACKLOG.md` rather than
> fixed on a hunch. `sw.js` `CACHE_NAME` bumped v45→v46; `dist/` rebuilt.
> Section 6 remains — see `docs/tasks/T62-art-pass-depth-and-scale.md`
> Findings.

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
| T53 | [Run stats and a score](tasks/T53-run-stats-and-score.md) | — | `DONE` |
| T54 | [Persistent high-score table](tasks/T54-high-score-table.md) | T53 | `DONE` |
| T55 | [Microtubule upgrades](tasks/T55-microtubule-upgrades.md) | T54 | `DONE` |

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
