# Backlog

Incidental findings. **Append here instead of fixing things outside your task's
scope** (`AGENT_CONDUCT.md` §1.2).

Format: one line per item — what, where (function name), and why it matters. Add
a date. Do not remove items; strike them through and note the task ID that fixed
them.

---

## Open — found during the 2026-08-02 code review

- **Dead code branch.** `checkArcCollision()` handles `hb.type === 'poly'`, but
  `drawArcs()` only ever pushes `{type:'path'}` into `centralHitboxes`. The poly
  branch is unreachable. Do not delete without confirming no future task needs it
  (T14's malignant mass could plausibly reuse it). — 2026-08-02

- **`run_test.py` has hard-coded Windows paths.** The `cwd` for the HTTP server
  and the screenshot `output_dir` are absolute paths to one machine
  (`c:\Users\au516150\...`). The script cannot run anywhere else. Superseded: `tools/soak.py`
  and `tools/verify_harness.py` replace it; `run_test.py` is now unused legacy. — 2026-08-02

- **`walkthrough.md` describes Phase 2 as complete, but none of it is in the
  code.** See `docs/tasks/P01-asset-pipeline-parked.md` for the full analysis.
  Owner decision needed on whether to annotate or move that section. — 2026-08-02

- **`Development_plan.md` documents dev keys that do not exist.** It claims `\`
  for god mode and `]` for +15s; the code uses `` ` ``/`~`/`½` and `Tab`.
  Addressed by T10. — 2026-08-02

- **Self-neck immunity constants disagree.** `checkCollision()` uses
  `skipFrames = 15` (effective window 16); `raycast()` hard-codes 16. The sensor
  and the physics differ by one frame. Addressed by T08. — 2026-08-02

- **`updateVesicles()` spawn is gated on `window.golgiData`.** If the Golgi is
  destroyed or the cache is null, vesicle spawning stops entirely. Confirm this is
  intentional (it plausibly is — the Golgi *is* the vesicle source) and document
  it, or make the dependency explicit. — 2026-08-02

- **`world.scale` is set in two places with different values.** `0.3` at init and
  `0.5` in `startRound()`, before `updateCamera()` takes over and lerps. Harmless
  but confusing; worth a comment explaining which is the intended first frame.
  — 2026-08-02

- **`checkCollision()` calls `players.find()` per grid item.** Currently cheap
  because segment counts are low, but it is a linear scan inside the hottest loop
  in the file. T01 hoists it in `raycast()`; the same hoist should be applied here
  if T06a shows it mattering. — 2026-08-02

- **Incremental spatial-grid updates.** `rebuildSpatialGrid()` is a full rebuild
  every frame — correct by construction, and that is worth a lot. Only consider
  incremental updates if T06a's profiling shows the rebuild as a genuine hotspot
  *after* T07's trace cap has landed. Incremental removal is where bugs hide.
  — 2026-08-02

- **`mitosis.cellB` never gets `radiusX`/`radiusY` fields**, but the outer-membrane
  wall-bounce in `updateVesicles()` (the `isOutsideCell` branch, pre-existing, not
  touched by T15) reads `nearestCell.radiusX`/`radiusY` and will get `NaN` there
  whenever a vesicle bounces off the wall while `mitosis.cellB` is the nearer cell.
  T15's new gravity-well code only reads `nearestCell.x`/`y`, so it does not hit
  this; found while reusing the same `nearestCell` pattern. — 2026-08-06

---

## Deferred design ideas

- Trace fade-out when trimmed by T07's cap, instead of a hard pop. Phase 4 juice.
- Weight necrotic organelles (T13) higher than drifting ones in the bot's hazard
  scoring — a permanent wall deserves more caution than something that will move.
- Bot should deliberately target the malignant mass (T14) while in `attack` mode.
  Currently `attack` is only entered near traces with a speed power-up, so bots
  will essentially never shatter it.
- Particle burst on malignant-mass block shatter (T14) — belongs with T17.
- ~~Extend additive blending beyond the trails and Golgi.~~ Written up as **T21**.
  Note the finding that came out of scoping it: roadmap 2.2's three literal
  targets (head cores, active traces, vesicle drop zones) are **already
  satisfied** — heads and traces are drawn into the additive `trailGlow`/
  `trailCore`, and the Golgi cisternae are additive. T21 is an extension beyond
  2.2's wording, not a gap in it.
- Per-viewport screenshake in split-screen mode (T16 applies shake to the shared
  composite only).
- Gravity well (T15) pulling players as well as vesicles — explicitly *not* what
  the roadmap says, and it would fight the steering model. Owner call.

---

## Found while unblocking the scheduled routine — 2026-08-02

- **The game was never actually self-contained.** `AGENT_CONDUCT.md` §2 claimed
  it "must keep working from `file://`", but the two `<script>` tags loaded
  PixiJS from cdnjs and pixi-filters from jsdelivr — so opening the file offline
  never worked, and sandboxes whose egress policy blocks those hosts could not
  run the game at all. Both libraries are now vendored in `vendor/` (fetched via
  `npm pack`, which is on the proxy allowlist). Verified: over `file://` the
  console is completely clean. **Never point these back at a CDN.**

- **Software rendering is slow.** No GPU in the sandbox, so game time runs at
  ~0.11x real time at 1280x1024 and ~0.38x at 640x480. Disabling the bloom
  filter changes nothing — the cost is rasterisation. Several task files ask for
  "5 minutes" or "10 minutes" of observation; those cannot be done in one
  10-minute invocation and must be split or fast-forwarded. Worth revisiting
  those durations task by task.

- **`startRound()` reads config from the DOM selects, not from the globals.**
  Setting `currentMode`/`aiCount` and calling `startRound()` silently keeps the
  previous configuration. Already flagged in T19; the harness handles it.

- **A `players=1, bots=1` round ends in seconds.** Nothing steers the human, it
  drives into the membrane, and one survivor ends the round. Use `bots=3` or
  `immortal=True` when observing. Cost us one hung verification run.

- **`favicon.ico` 404 is the one expected console entry** over `http://`. It
  does not appear over `file://`. The harness filters it — note the URL is in
  the console message's `location`, not its `text`.

---

## Found while hardening the fuzzer (T04) — 2026-08-03

- **`performance.memory.usedJSHeapSize` climbed steadily across an 8.4-minute
  fuzz soak** (≈61MB → ≈486MB over 22 restarts), while `fuzzStats.worldChildren`
  stayed flat across restarts (~700 right after `startRound()`, ~1300-1400
  mid-round, both bands repeating identically many rounds apart). The flat
  `worldChildren` says this is **not** the PixiJS display-object leak T05
  targets. It's more likely GC lag from per-frame trace-point/vesicle/particle
  allocation under the fuzzer's dilated clock, but T04 only measures — T06a's
  longer soak should watch whether `heapMB` keeps climbing past ~500MB or
  plateaus once GC catches up.

## Found while scoping Phases 6 and 7 — 2026-08-03

- **Gap and vesicle spawn are frame-rate dependent, not time dependent.**
  `GAP_CHANCE = 0.008` is rolled once per player per *frame*; `GAP_LENGTH = 12`
  counts *frames*, not distance; and both vesicle-spawn sites roll
  `Math.random() < 0.008` per frame. A device at 30fps therefore gets half the
  gaps, half the vesicles, and gaps half as long in world distance. This is a
  live fairness bug on any slow device, not just a multiplayer problem.
  Addressed by T28. — 2026-08-03

- **`drawTraces()` is O(total trace points) every frame, twice.** It clears and
  re-emits every point of every trace for both `trailGlow` and `trailCore`. At
  60fps, 4 players, 2 minutes ≈ 28,800 points ≈ 57,600 `lineTo` calls per frame,
  growing for the whole round — and `trailGlow` carries a `BlurFilter`, so the
  growing path is re-filtered too. Addressed by T25. — 2026-08-03

- **Simulation and rendering are fused**, so the game cannot be stepped without a
  renderer. Blocks multiplayer entirely and caps soak-test throughput at ~0.38x
  real time. Addressed by T22; `AGENT_CONDUCT.md` §4.4a stops new systems from
  adding to the debt. — 2026-08-03

- **No pause exists.** There is `app.ticker.stop()` on solo game-over and an
  `isPlaying` flag, but nothing player-initiated. T24 adds one for mobile; note
  that a local pause must not pause remote players once Phase 7 lands.
  — 2026-08-03

- **Render interpolation between fixed simulation steps** — deferred out of T28
  deliberately so the fixed step can be validated alone. Worth doing once T28 is
  stable, especially for high-refresh displays. — 2026-08-03

- **Host migration** for Phase 7 — explicitly out of scope for v1 (T32 ends the
  match if the host leaves). Revisit only if sessions prove long enough for it to
  matter. — 2026-08-03

## Found while doing T05 (PixiJS lifecycle) — 2026-08-04

- **`drawArcs()`'s own `rotatingContainer.removeChildren()`** (top of the
  function) is a second, un-purged teardown of the same container T05 fixed in
  `generateMap()`. It's a no-op when called from `generateMap()` (the container
  is already empty by then), but it's also called stand-alone from the
  arc-shatter path in `gameLoop`/`updateMitosis` every time an ER/Golgi arc
  breaks mid-round, discarding real `Graphics` built that round without
  destroying them. Left alone here because it wasn't in T05's task file and it
  overlaps T09 (ER persistence), which also touches `drawArcs()`. — 2026-08-04

- **Task-file drift:** T05's task file attributes the organelle re-parent site
  (`organellesLayer.removeChildren(); ...; organelles.forEach(o =>
  organellesLayer.addChild(o.sprite));`) to `drawMitosisVisuals()`. The code
  string matched exactly, but it actually lives in `updateMitosis()`'s mitosis
  merge path, not `drawMitosisVisuals()`. Left in place with a comment per the
  task's instruction; noting here so nobody goes looking for it in the wrong
  function. — 2026-08-04

## Found while running T06a soak run B — 2026-08-04

- **`tools/soak.py` can never write `COMPLETE` for an `immortal=True` config,
  no matter the `--minutes-cap`.** `fuzzStats.rounds` only increments in
  `gameLoop`'s round-end branch, which requires `activePlayers.length <= 1`
  (solo) or `<= 1` (multi) — i.e. players dying. `immortal=True` sets
  `godMode`, which disables every `!devMode`/`!godMode` death check, so no
  player ever dies and `rounds` stays `0` for the run's entire duration
  (confirmed: `rounds=0` at every sample across a full 2400s/40min run B).
  `soak.py`'s completion check is `s["rounds"] >= a.rounds`, so with the
  `--rounds 1` the task file specifies, the target is mathematically
  unreachable and the run always ends `INCOMPLETE` at the wall-clock cap,
  regardless of how long the cap is. T06a's own procedure ("give it `--rounds
  1 --minutes-cap 40` and let the wall-clock cap end it") contradicts the
  driver's actual behavior, which treats a cap-hit as failure for every
  config, not just B. Not patched here per `AGENT_CONDUCT.md`'s instruction
  not to modify `tools/soak.py` mid-series; needs an owner decision — e.g. a
  `--allow-cap-complete` flag, or accepting round 0 as done for immortal runs.
  See `## Blocked` in `docs/tasks/T06a-soak-measurement.md`. — 2026-08-04

## Found while unblocking T06a Stage B — 2026-08-04

- **RESOLVED: `tools/soak.py` could never complete an immortal config.** Run B
  sets `immortal=True`, so `godMode` disables every death check, so
  `fuzzStats.rounds` never increments, so the only completion path
  (`rounds >= target`) was unreachable at any cap. The task file said "let the
  wall-clock cap end it" while the driver treated the cap as failure — a direct
  contradiction between prose and tool. Fixed: per-config `done_when` of
  `("rounds", n)` or `("minutes", m)`, plus guards that refuse an
  immortal+rounds config and refuse a mismatched `--rounds`/`--minutes`
  override. Cost one wasted 40-minute run. — 2026-08-04

- **A second memory leak, not the display-object one.** Run A's heap sawtooth
  *floor* rises monotonically 44 → 124 MB over 58 rounds (~1.4 MB/round) while
  `worldChildren` stays flat at 1310–1388. A rising floor is retention; GC lag
  would show rising peaks over a stable floor. T05 fixed the PixiJS
  display-object leak, so this is something else — closures holding reassigned
  arrays, accumulated listeners, or per-round state on `window` are the
  candidates. Full analysis in `docs/tasks/T06a-soak-measurement.md`. Needs a
  task once T06b weighs it. — 2026-08-04

## Glow quality tiers landed early — 2026-08-04

- **`Glow: Low / Medium / High` dropdown added at owner request**, ahead of
  T26. Drives `QUALITY_TIERS` + `applyGlowQuality(tier)` covering the
  `AdvancedBloomFilter` and the trail-halo `BlurFilter`. **Default is Low** —
  the original tuning (now High) washed out the scene: at High the ER reads as
  one solid glow blob and mitochondria in the periphery are barely visible,
  which is a legibility problem, not only a taste one. T26 still owns folding
  the remaining effects in plus auto-detection. — 2026-08-04

- **`updateUI()` is never called at page load**, only from the select
  `onchange` handlers and `startRound()`. Anything that needs to be applied at
  startup must call it explicitly — `applyGlowQuality('low')` does. Worth
  remembering for any future menu setting. — 2026-08-04

## Found while doing T07 (trace cap) — 2026-08-05

- **Cross-player self-immunity indices can go stale mid-frame.** `rebuildSpatialGrid()`
  runs once at the top of `gameLoop`, but `checkCollision()`/`raycast()` compare
  its snapshotted `item.s` against `other.traceSegments.length` read *live*
  (`checkCollision()` ~line 1690, `raycast()` ~line 1414). If an earlier-processed
  player in the same frame shifts whole segments off its own front (a trim, or
  the pre-existing `deleteOldestTrace()` power-up wipe) or pushes a new segment
  (gap end / ghost end), a later-processed player's collision check against that
  first player's trace uses a length that no longer matches the indices baked
  into the grid snapshot — `item.s === other.traceSegments.length - 1` can
  misfire either way for one frame. Pre-dates T07 (any `deleteOldestTrace()` call
  already had this exposure); T07's per-frame `trimTraceToCap()` doesn't change
  the mechanism, but only engages this path once a player is actually at
  `MAX_TRACE_POINTS`, which is rare with the conservative cap landed here.
  Verified this frame's *own*-trace immunity check is unaffected (each player's
  own collision check runs before its own trim within the same iteration), so
  this is specifically an opponent-trace edge case. Not fixed here — out of
  scope for T07 and no observed failure in testing. — 2026-08-05

## Found while doing T09 (ER persistence) — 2026-08-05

- **Golgi layer `thick` re-randomizes on every `drawArcs()` redraw and feeds
  `centralHitboxes`** (`thick = 12 + Math.random() * 3` inside the per-layer
  loop, not stored in `window.golgiData`). Unlike the ER's random layout
  angle/radius jump this fixes, the Golgi's cached `x/y/rot` and `sacPoints`
  keep the shape stable — only the hit-test half-width jitters by up to 3px
  around a fixed centerline on every arc shatter, a much smaller and
  lower-severity version of the same bug class. Out of scope for T09 (ER
  only); would need `thick` folded into `window.golgiData.layers` the same
  way `sacPoints` already is. — 2026-08-05

- **ER ribosome dots re-randomize their on/off pattern and jitter their
  radius on every `drawArcs()` redraw** (`Math.random() > 0.4` gating each
  dot, `2 + Math.random() * 1.5` for its size). Purely decorative — no
  `centralHitboxes` entry depends on them — so left alone per this task's own
  instruction (step 4): a cosmetic flicker on shatter, not a fairness bug.
  — 2026-08-05

## Found while doing T12 (Gen 2 membrane calcification) — 2026-08-05

- **The mitosis "stray player" kill check still gates on `devMode`, not
  `godMode`.** In `updateMitosis()`'s split-completion block, a player left
  outside both the bridge and Cell B is teleported to safety `if (devMode)`
  and killed otherwise — unlike every other death check in the file, which
  T04 moved to `godMode`. Concretely: calling the verification harness's
  `immortal=True` (which sets `godMode`, not `devMode`, since T04 landed)
  does **not** protect a straggler from this specific kill, unlike every
  other hazard. Found because it explained an otherwise-surprising
  `alive` drop during an "immortal" T12 mitosis test. Out of scope for T12;
  a one-line `devMode` → `godMode` fix (or `devMode || godMode`) whenever
  someone next touches `updateMitosis()`. — 2026-08-05

## Found while doing T13 (Gen 2 organelle necrosis) — 2026-08-05

- **Bot avoidance weight doesn't distinguish necrotic from drifting
  organelles.** `updateBotAI`/`getRayWeight` treats every `'organelle'` ray
  hit identically, but a necrotic one is a permanent wall while a drifting
  one will move out of the way on its own — a necrotic hit deserves a higher
  avoidance weight. Explicitly out of scope for T13 (see that task file's
  "Bot awareness" section); revisit once T03's hazard-weighting channels can
  take hit subtype into account. — 2026-08-05

## Found while doing T14 (Gen 3 malignant mass) — 2026-08-06

- **Shattered mass blocks just disappear — no particle burst.** Every other
  destructible thing in the game (organelles, Golgi arcs) spawns vesicles or
  a burst on destruction; the malignant mass does not. Explicitly deferred to
  T17 (particle emitter splash system) per T14's own design doc (§5). —
  2026-08-06

- **Bots essentially never enter `'attack'` targetMode near the malignant
  mass**, so they will almost never shatter it — `updateBotAI` only flips to
  `'attack'` near a trace with an active speed power-up (T03's logic), with
  no awareness of the mass at all. Out of scope for T14 per its own design
  doc (§6); the mass's avoidance behaviour (steering around it) works fine
  without this, but a bot will never proactively clear a path through it. —
  2026-08-06

## Phase 1 gate: soft FAIL on memory — 2026-08-04

- ~~**Retained memory across rounds, not display objects.**~~ **RESOLVED by
  T07 — 2026-08-06.** Run A's heap sawtooth floor rose 44 → 124 MB over 60
  rounds (~1.4 MB/round) at `30ec41a` while `worldChildren` held flat at
  1292–1388. Re-measured at `8762fcf` (T07's trace cap + T08–T17 landed since)
  over a comparable ~1063s/453-round span: floor is now flat, 41.7–48.2 MB
  across 6 windows, no upward trend. `worldChildren` still flat, same band as
  before. No code change was needed. Full before/after tables and the ruled-out
  candidate list are in `docs/tasks/T06c-heap-leak-hunt.md`'s `## Findings`.

## Found while doing T20 (control-mapping splash) — 2026-08-06

- **`startRound()` never resets `activeCell.x`/`activeCell.y`.** They start at
  `{1500, 1500}` (module init, line ~427) but a completed mitosis event
  permanently reassigns them to `mitosis.cellB`'s position (`updateMitosis()`,
  ~line 2654). `startRound()` resets `generation`/`baseRadiusX`/`baseRadiusY`
  but not `x`/`y`, so a manual restart (or the fuzzer's `setTimeout(startRound,
  0)`) after any round that advanced past Gen 1 spawns the next round's players
  offset from the drifted center instead of the map's true origin. Found while
  hoisting `playerConfigs` for the splash (T20): the spawn positions had to
  become `activeCell.x/y + dx/dy` offsets specifically because this value is
  not stable across rounds. Not fixed here — out of T20's scope and it isn't a
  collision-safety bug (the map itself is still generated relative to whatever
  `activeCell.x/y` holds), but it likely explains any "map looks off-center on
  restart after a long game" reports.

## Found during T19 — 2026-08-06

- ~~**`#ui` panel overflows below ~410px viewport width.**~~ **RESOLVED by
  T24 — 2026-08-07.** `#ui { min-width: 400px; }` predates T19 and already
  clips the rightmost control (the Fullscreen button) off-screen at narrow
  widths like 360px, independent of the Quick Play button added in T19
  (verified against the pre-T19 file). Confirmed fine at 600px+. Worth a
  look whenever mobile/responsive layout (T23) is tackled.
- **Mid-round `drawArcs()` orphan is still real, still unfixed.**
  `rotatingContainer.removeChildren()` at the ER/Golgi arc-shatter path
  (`gameLoop` ~L3536) discards the previous `structGraph` `Graphics` without
  `.destroy()`ing it, same as flagged doing T05/T09. Confirmed via T06c that
  run A's soak never exercises this path (mitosis needs 240s survival time to
  trigger, 60+ dilated game-seconds after that to reach `'narrowing'` where
  arcs shatter; run A's rounds average ~9s dilated game time before a player
  dies) — so it isn't what run A's flat floor is measuring one way or the
  other. Worth a task if a future immortal-mode soak (run B) or a
  longer-survival config shows a floor component tracking arc-shatter counts.
  — 2026-08-06

## Found during T24 (touch-friendly menu and HUD) — 2026-08-07

- **Hover-to-peek can get stuck open if the mouse never crosses the revealed
  panel.** `mouseenter` is bound to `#ui-trigger` (full-width, 30px-tall top
  strip) but `mouseleave` is bound to `#ui` itself (the centered panel,
  narrower than the trigger strip). If the mouse enters the trigger strip
  outside the panel's horizontal footprint (e.g. near the left/right screen
  edge) and then moves straight down into the game without ever passing over
  the now-revealed `#ui` box, no `mouseleave` ever fires (the browser only
  fires it once the pointer has actually entered the element), so the menu
  stays visible until the mouse happens to cross it later. Confirmed present
  on the pre-T24 code too (bisected with `git stash`), so it isn't something
  this task introduced — left alone per scope discipline. A fix would need
  either widening `#ui-trigger` to always match `#ui`'s current footprint, or
  moving the reveal/hide pairing onto the same element.

## Found during T25 (incremental trace rendering) — 2026-08-07

- **`trailGlowRT`/`trailCoreRT` do not follow the world past the mitosis
  snap, and are not sized to include `mitosis.cellB`.** `rebuildTraceRT()`
  sizes and positions the accumulation buffers around
  `activeCell.x/y ± (baseRadiusX/Y + TRACE_RT_PADDING)` — deliberately just
  the single active cell, matching the task file's own "world is ~2800x2400"
  sizing guidance. But `updateMitosis()` reassigns `activeCell.x`/`y` to
  `mitosis.cellB`'s position at the snap (~120s into a mitosis event,
  `gameLoop` line ~2935 pre-T25), and for the ~120s *before* that snap,
  players are already moving through the bridge into `cellB`, which sits up
  to 3400px outside the pre-snap RT window (`updateMitosis()`'s `offset`
  constant). Trace geometry laid down in the bridge/cellB during that window
  falls outside the RT's fixed pixel bounds and will not render (collision
  is unaffected — `traceSegments`, `checkCollision()` and `raycast()` never
  read the RT). Nothing forces a recenter+redraw at the mitosis snap either,
  so a trace that survives the snap (per-player, if the player made it to
  Cell B) keeps pointing into geometry the buffer no longer covers. Not
  triggered by any of T25's own verification (mitosis needs 240s survival
  time; longest verification round was 183s) or by this codebase's short
  soak runs so far. Fix would need `rebuildTraceRT()` called again (recenter
  + full redraw, same as the front-trim path) both when `mitosis.cellB` is
  computed and at the snap, with the origin/size covering the union of both
  cells while a division is in progress.

## Found during T23 — 2026-08-07

- ~~**`#ui` panel overflow is now real, not just theoretical.**~~ **RESOLVED
  by T24 — 2026-08-07.** The T19 note above flagged `#ui { min-width: 400px; }`
  as overflowing below ~410px and said it was "worth a look whenever
  mobile/responsive layout (T23) is tackled." T23 adds the
  `<meta name="viewport" content="width=device-width...">` tag the game
  previously lacked; before that tag existed, mobile browsers laid out at a
  virtual ~980px width, so the 400px-min panel had headroom and never
  visibly clipped. With real device-width layout now active, a 390px phone
  (`document.getElementById('ui').scrollWidth` measured at 460px against a
  390px viewport, `body { overflow: hidden }`) genuinely clipped part of the
  landing menu off-screen with no way to scroll to it. Confirmed via
  `tools/verify_harness.py`, screenshot at `/tmp/verify/t23_menu_390.png`.
  T24 fixed it: `min-width: min(400px, 94vw); max-width: 94vw;` instead of a
  flat `400px`, so desktop is unchanged (`min(400, 94vw)` still evaluates to
  400 at any normal desktop width) while narrow phones shrink the panel and
  let `.controls`' existing `flex-wrap` reflow the buttons instead of
  clipping them. Re-verified at 390px and 360px: `scrollWidth` no longer
  exceeds the viewport at either.

## Board-mechanics bug — 2026-08-07

- **T22 sat `BLOCKED` with its dependency satisfied.** T22 depends on T06a,
  which completed on 2026-08-05, but T06a's `Definition of done` listed only
  "T07, T11, T16 → READY" — written before T22 existed. The session that
  finished T06a correctly flipped exactly what it was told to, and nothing
  flipped T22. Because T06b gates nothing downstream, this left the routine with
  **no `READY` work at all**, so it would have idled indefinitely.
  Fixed 2026-08-07; `docs/TASKS.md` now carries a standing rule to update the
  upstream task's checklist whenever a new dependent task is added. — 2026-08-07

- **T06c resolved the Phase 1 memory question without a code change.** Its
  Step 0 re-measurement showed the heap floor flat at 41.7–48.2 MB across six
  windows, versus the original monotonic 44 → 124 MB climb — T07's per-player
  trace cap had already fixed it. The "re-measure before investigating" step
  paid for itself: it prevented a full session hunting a leak that no longer
  existed. T06b's verdict can be a clean PASS on this evidence. — 2026-08-07

## Owner playtest — 2026-08-07

Eleven findings, written up as T33–T42. Diagnoses established before writing:

- **Trace invisible past the bridge (T33)** — `rebuildTraceRT()` sizes the trace
  RenderTexture to `activeCell.baseRadiusX/Y + 150`, but `mitosis.cellB` is
  ~3400px away, so the bridge and Cell B fall entirely outside the buffer.
  Collision is unaffected, so players die to traces they cannot see. T25
  regression.
- **Pause already exists (T40)** — T24 added `#pauseMenuBtn`, `togglePauseMenu()`
  and a `paused` flag, with no touch-only CSS gate. The owner still never found
  it, so this is discoverability, not a missing feature.
- **Target mode is nearly inert (T36)** — `targetMode === 'attack'` is consulted
  in exactly one gameplay place, T14's mass shatter. Nothing in the vesicle
  path branches on it, yet `controlsText` advertises "Toggle Boost Target". The
  behaviour the owner remembers (red sends the pickup to an opponent) is absent.
- **Necrosis changes almost nothing (T38)** — organelles were already lethal
  before T13; `necrotic` only alters palette and motion. T13 implemented its task
  file faithfully — the task file was what lacked a mechanic. My omission.
- **Double membrane (T37)** — T12 offered "leave the baked membrane, it reads as
  the old wall" as an option and it was taken; the owner judged it wrong. The
  organelle bounce flips both velocity components unconditionally against a
  moving wall, causing per-frame snap/reverse jitter.
- **"Tumour" is biologically impossible inside a single cell (T39)** — a tumour
  is many cells. Recommended reframing as a protein aggregate / aggresome, which
  is a real intracellular pathology and fits the generation ladder.

## Necrosis design settled — 2026-08-07

- **T38 rewritten to the owner's combined design**: necrotic organelles fuse into
  clusters, clusters shed lethal debris at a rate that scales with size, and red
  mode breaks off one member per hit. Each of my four original single-mechanic
  options had a real flaw — accretion had no counter-play, shedding produced
  arbitrary deaths — and combining them cancels both, because debris volume
  becomes player-controlled. Neglect compounds, management pays.
- **Key implementation constraint recorded in the task:** fusion is *clustering*,
  not merged geometry. Members keep their existing hitboxes and gain a
  `clusterId`, so `checkCollision()` and `raycast()` need no change for the
  cluster itself, and "break it bit by bit" falls out for free. Merging hitboxes
  would have invented a new collision primitive needing both paths re-verified.
- **Cross-task visual constraint:** T38's clusters are mineralised grey and
  angular; T39's aggregate is soft amber protein. They share the "red mode breaks
  dead matter" rule on purpose, but must be distinguishable at a glance. Noted in
  both task files. — 2026-08-07

## Found during T40 (pause discoverability) — 2026-08-08

- **`pointer-events: none` made a fixed-position, high-z-index overlay div
  invisible in this sandbox's headless/software-rendered Chromium**, even
  though it stacked above the canvas by every CSS rule (`z-index`, DOM order,
  no clipping ancestor). `elementFromPoint` at its own center returned the
  `<canvas>` beneath it; raw pixel-sampling a screenshot found no trace of the
  div's background or text, even with a loud red test background; Playwright's
  own actionability check independently agreed ("element is not visible").
  Isolated A/B testing (toggling only `pointer-events`, nothing else) showed
  removing it was sufficient — same element, same z-index, then painted and
  hit-tested correctly. `#pauseMenuBtn` (a `<button>`, never had
  `pointer-events` set) was unaffected throughout, which is why the existing
  pause button always rendered fine and this was easy to miss. Root cause not
  fully diagnosed — plausibly a compositing-layer ordering quirk specific to
  this environment's software WebGL path (SwiftShader) — but reproduced
  cleanly and is worth knowing about: any future task stacking a
  `pointer-events: none` overlay above the canvas should verify with a real
  screenshot pixel-check (not just `getComputedStyle`) in this harness, since
  the CSSOM will report the element as displayed and opaque while it silently
  fails to paint. Whether this also affects real (non-headless, GPU) browsers
  is unverified — no way to test that from this environment. Full repro steps
  in `docs/tasks/T40-pause-discoverability.md`'s `## Findings`. — 2026-08-08

## Open — found during T34

- **Per-frame `new PIXI.Graphics()` allocation in the split-screen branch of
  `updateCamera()`.** The viewport border is built fresh (`new PIXI.Graphics()`,
  `lineStyle`, `drawRect`) once per alive player, every frame, then discarded
  for GC — up to 4 allocations/frame in split mode, contrary to AGENT_CONDUCT
  §5's no-allocation-in-the-hot-path rule. Content and size are identical across
  viewports and frames; a single reusable `Graphics` object drawn once (or a
  cached texture) would cover it. Left out of T34's diff to keep it to the
  bloom-per-viewport fix the task asked for; the bloom fix's effect could not be
  confirmed in wall-clock terms in the sandboxed (GPU-less) test environment, so
  this may be worth a follow-up task if the owner still sees stutter after T34
  lands. — 2026-08-07

## Owner playtest round 2 — 2026-08-07

- **`golgiTimer` has never been wired up.** The blue vesicle grants it, the HUD
  draws a bar for it, and it is decremented every frame — but no collision path
  has ever read it. `git log -S golgiTimer` returns only the initial import
  `4bf057f`. So the single-pickup "pass through the Golgi" effect grants
  literally nothing, and has not since the repo began. The 3x blue combo
  (`ghostTimer`) does work. Written up as **T43**. — 2026-08-07

- **`RenderTexture` does not inherit `antialias` from the renderer.** The app is
  created with `antialias: true`, but the split-screen viewport textures are
  `RenderTexture.create({width, height})` with no `multisample`. Shared mode gets
  MSAA, split mode does not — which is why split "looks lower resolution". A
  general trap for any future RenderTexture in this codebase, including T25's
  trace buffers. Written up as **T44**. — 2026-08-07

- **T34 was right to report apply-count rather than wall-clock.** With no GPU in
  the sandbox, rasterisation dominates and timing numbers do not show filter-pass
  wins. Countable proxies (draw calls, filter applies, render-target bytes,
  allocations) are the honest evidence here; wall-clock is a secondary note.
  Worth remembering for every future perf task. — 2026-08-07

## Found while doing T43 (golgiTimer wiring) — 2026-08-08

- **Possible neck-immunity edge case at Speed: Very Fast (3.5), unconfirmed.**
  Regression-sweep script: after 10s of unsteered play at speed 3.5,
  `checkCollision(near.x, near.y, p)` returns `true` (lethal) for `near` = the
  most-recently-pushed point of the player's own last trace segment, where at
  speeds 1.5 and 2.5 the identical check returns `false` as expected. Bisected
  with `git stash` against the pre-T43 file at the same commit: **identical
  result on unmodified code**, so this is not something T43's `golgiTimer`
  change touches or introduces — T43 never reads `traceSegments`, `isOwnNeck`,
  or `NECK_LENGTH`. Could be a genuine `NECK_LENGTH`/`isOwnNeck` edge case at
  large per-frame step sizes, or could be a test-methodology artifact (probing
  the exact last-pushed point rather than a real lateral near-miss trajectory
  — nearby, non-neck trace geometry from the same short unsteered run could
  legitimately be within `TRACE_HITBOX` of that point). Not investigated
  further — out of scope for T43. Worth a real in-browser near-miss playtest
  at Very Fast before trusting either explanation. — 2026-08-08

## Found while doing T44 (split-screen quality/cost) — 2026-08-08

- **`trailGlowSprite`/`trailCoreSprite` are never culled per split-screen
  viewport.** They default to `cullable = false`, so every viewport capture
  samples the full trace RenderTexture (up to ~3550x1350 during mitosis, see
  T33) even when most of it is off that viewport's visible rect. Setting
  `cullable = true` would let PIXI skip the draw entirely when a viewport's
  frame doesn't intersect the sprite's bounds. Not applied in T44: both
  sprites carry a `BlurFilter`, whose bleed extends the effectively-visible
  area slightly past the geometric bounds PIXI's culling test uses, and this
  sandbox has no GPU to visually confirm glow doesn't clip at a viewport
  boundary as a result. Worth trying with real-browser verification. — 2026-08-08

- **`MSAA_QUALITY` RenderTextures silently resolve to a blank capture on the
  WebGL2 backend available in this sandbox** (`MAX_SAMPLES` reports 4,
  `webGLVersion` is 2, no GL error, `extract.pixels()` reads back all zero).
  T44 added a one-time capability probe (`splitMSAASupported`) that falls back
  to `MSAA_QUALITY.NONE` when this happens, so split-screen never silently
  goes blank — but it means antialiasing has not actually been exercised
  end-to-end in any environment available to an agent session. Worth an
  owner playtest on real hardware to confirm MSAA actually engages and looks
  right there (the probe should report `true` and viewport edges should look
  smoother at Medium/High than they did before T44). — 2026-08-08

## Found while doing T41 (how-to-play tutorial) — 2026-08-09

- **Vesicle-effect magic numbers are not named constants.** The pickup block
  (`checkCollision`'s caller loop, "3. Vesicle Collection Logic") hand-codes
  the golgi/speed cap (`15.0`), the ghost/speed chain-combo cap and window
  (`10.0`, `3.0`), and the blue/red pickup-count thresholds (`blueCount >= 3`,
  `redCount >= 5`, `redCount === 3`) as bare literals — only `EFFECT_DURATION`
  (the base `+10s` per pickup) is a real constant. T41's Vesicles section
  transcribes these numbers directly from that code (verified by reading, not
  guessed), but they can drift silently if this block is edited later, since
  nothing would point back at the tutorial text. Left alone here: the pickup
  block is dense and high-traffic, and hoisting every literal there is a
  bigger, riskier diff than a tutorial task should carry. If someone touches
  vesicle economy tuning next, consider naming these too — `NUCLEUS_RADIUS`,
  `MITOSIS_INTERVAL`, `MITOSIS_SWEEP_DURATION`, `INFECTION_INTERVAL`,
  `INFECTION_WARNING`, `CALCIFY_RATE`/`CALCIFY_FLOOR` were hoisted by this
  same task and are the model to follow (see `260703_Cellsnake.html` near
  the `NECROSIS_*` constants).
- **An interactive tutorial level still isn't built.** T41 deliberately scoped
  down to a static Help panel per its own instructions ("build the explanation
  first"). A scripted walkthrough round (spawn a lone player in a stripped-down
  arena, narrate each hazard as it's encountered) would need its own state
  machine and is a materially larger project — logged here per T41's explicit
  ask, to revisit if the static guide turns out not to be enough.

## Found while doing T42 (tubulin-dimer trace) — 2026-08-09

- **`gameLoop()` calls `drawTraces()` twice every unfrozen frame.** Once inside
  the `!isCellFrozen` block (before that frame's player-movement loop runs,
  so before any new trace points exist) and once unconditionally at the very
  end (after movement). `trailGlow`/`trailCore` are `.clear()`d at the top of
  every `drawTraces()` call, so the first call's head/aura/tip drawing is
  fully overwritten by the second and never visible on screen — wasted work
  every frame (roughly double the per-frame head/aura/tip cost, though
  `accumulateTraceRT()`'s own cost is cheap either way since the first call
  finds nothing new to bake). Not touched here — out of scope for a
  rendering-only task and risky to change without understanding why two
  calls exist in the first place. — 2026-08-09

- **This sandbox's headless Chromium reports `navigator.hardwareConcurrency
  = 4`**, which `detectInitialQuality()` treats as "weak device" and starts
  every round at the `low` quality tier — whose `particleBudget` is `0`. The
  entire T17 particle system (locomotion splash, vesicle-pickup bursts, and
  now T42's depolymerisation burst) is silently inert in this environment
  unless a test explicitly calls `applyQuality('medium'|'high')` first. Not a
  bug — `low`'s 0 budget is presumably intentional for genuinely weak
  devices — but worth knowing for any future particle-system verification in
  this harness: a `particleCount` that stays 0 for an entire run does not by
  itself mean the emission code is broken. — 2026-08-09

- **Drifting organelles are not culled when the membrane shrinks past them
  (T48).** T48 added a cull for `malignantMass.blocks` in the calcification
  block of `gameLoop`, but `updateDriftingOrganelles()` moves organelles on
  its own schedule with no equivalent check against
  `isOutsideCell(o.x, o.y, o.radius)`. The owner's Gen 3 screenshot that
  prompted T48 shows one organelle stranded outside the floor radius
  alongside the aggregate blocks — same visible defect, different
  subsystem, confirmed real but explicitly out of scope for T48. — 2026-08-09

- **`window.bgMask` (the cytosol container's mask, `generateMap()`) is baked
  from the round-start `activeCell.radiusX/radiusY` and never redrawn**, same
  root cause as T49's protrusions/`cellBg`/cytosol bug but for the mask that
  clips them. T49 fixed cytosol containment at the physics-position level (a
  blob's `x`/`y` are now kept inside the *current* ellipse every frame), which
  makes the stale, oversized mask a non-issue in practice — no blob's true
  position is ever far enough out for the gap between the current wall and
  the stale mask to show. Left as-is since T49's fix already closes the
  visible defect; flagging in case a future task removes or changes the
  containment logic and the stale mask becomes visible again. — 2026-08-09

- **`tools/verify_harness.py`'s `start_round()` silently accepts an invalid
  `speed` value.** The game's `speedSelect` only has options `1.5`/`2.5`/`3.5`
  ("Normal"/"Fast"/"Very Fast"); passing e.g. `"1.0"` or `"2.0"` sets the
  `<select>`'s `.value` to a non-existent option, which the DOM silently
  ignores (the select keeps its previous value) rather than throwing — a test
  written against the wrong speed strings gets a confusing result instead of
  an error. Worth a one-line assertion or docstring note in the harness for
  the next session. Found and worked around during T49's regression sweep
  (§7.6). — 2026-08-09
