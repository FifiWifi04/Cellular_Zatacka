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
  (`c:\Users\au516150\...`). The script cannot run anywhere else. Fixed as part of
  T06; if you touch it earlier, fix it then. — 2026-08-02

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
  if T06 shows it mattering. — 2026-08-02

- **Incremental spatial-grid updates.** `rebuildSpatialGrid()` is a full rebuild
  every frame — correct by construction, and that is worth a lot. Only consider
  incremental updates if T06's profiling shows the rebuild as a genuine hotspot
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
