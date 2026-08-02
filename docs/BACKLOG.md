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
- Extend additive blending to vesicle drop zones and player head cores. This is
  Phase 2.2 and is **independent of the parked asset swap** — it works fine on the
  current vector renderer. Low risk, could be its own task whenever wanted.
- Per-viewport screenshake in split-screen mode (T16 applies shake to the shared
  composite only).
- Gravity well (T15) pulling players as well as vesicles — explicitly *not* what
  the roadmap says, and it would fight the steering model. Owner call.
