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
> **Owner session 2026-08-09 reopened Track J with two playtest defects.** T46
> (Help did not pause) is already fixed. **Take T47 next** — T42's dimer motif
> is gated on a camera zoom that shared camera essentially never reaches, so the
> headline visual is off for whole rounds; it carries a design choice to make.
> After T47: **T22** (sim/render split), then Phase 7.**

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
| T22 | [Separate simulation from rendering](tasks/T22-sim-render-split.md) ⏳ *resumable* | T06a | `READY` |

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
| T28 | [Fixed-timestep simulation](tasks/T28-fixed-timestep.md) | T22 | `BLOCKED` |
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
| T47 | [Tubulin motif invisible in shared camera (zoom never reaches the LOD gate)](tasks/T47-dimer-lod-never-reached.md) | T42 | `READY` |

### Track K — Playtest design & features

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T38 | [Necrosis: fuse, shed debris, break apart in red mode](tasks/T38-make-necrosis-matter.md) | T36, T37 | `DONE` |
| T39 | [Replace the "tumour" with a protein aggregate; grow faster](tasks/T39-aggregate-not-tumour.md) | — | `DONE` |
| T41 | [How-to-play tutorial](tasks/T41-tutorial.md) | T36, T40 | `DONE` |
| T42 | [Trace as tubulin-dimer microtubule](tasks/T42-tubulin-trace.md) | T33 | `DONE` |

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
