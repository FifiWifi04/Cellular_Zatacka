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
