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

## Found during T19 — 2026-08-06

- **`#ui` panel overflows below ~410px viewport width.** `#ui { min-width:
  400px; }` predates T19 and already clips the rightmost control (the
  Fullscreen button) off-screen at narrow widths like 360px, independent of
  the Quick Play button added in T19 (verified against the pre-T19 file).
  Confirmed fine at 600px+. Worth a look whenever mobile/responsive layout
  (T23) is tackled.
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
