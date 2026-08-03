# Task Board — Cellular Zatacka

Sequential work plan. **Do one task per session, in order.** Read
[`AGENT_CONDUCT.md`](AGENT_CONDUCT.md) first — every time.

Target file: `260703_Cellsnake.html` (single file, no build step).

---

## How to use this board

1. Open this file. Find the lowest-numbered task with status **`READY`**.
2. Open `docs/tasks/<ID>-*.md` and follow it exactly.
3. When done and verified, change that task's status here to **`DONE`**, and
   change the next task's status from `BLOCKED` to `READY` **only if** its listed
   dependencies are all `DONE`.
4. Commit both the code change and this board update together.

Statuses: `READY` · `BLOCKED` (dependency not met) · `DONE` · `PARKED` (deferred
by owner decision) · `OWNER-RUN` (must be run by a human, not a scheduled agent).

**`OWNER-RUN` tasks:** a scheduled session must **skip** these and take the next
`READY` task instead. If the only remaining work is `OWNER-RUN`, report that and
stop. Currently only **T06b** (the Phase 1 PASS/FAIL verdict), because it is a
judgement about the project rather than a measurement. Its data collection was
split out into T06a, which a scheduled session *can* run — that is deliberately
what T07, T11 and T16 depend on, so the routine is never blocked waiting on a
human decision.

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
| T04 | [Separate god mode from fuzzer; harden fuzzer](tasks/T04-fuzzer-hardening.md) | — | `READY` |
| T05 | [PixiJS display-object lifecycle fixes](tasks/T05-pixi-lifecycle.md) | — | `READY` |
| T06a | [Soak measurement — collect gate evidence](tasks/T06a-soak-measurement.md) ⏳ *resumable* | T04, T05 | `BLOCKED` |
| T06b | [Phase 1 gate verdict — PASS/FAIL](tasks/T06b-gate-verdict.md) 👤 *owner-run* | T06a | `BLOCKED` |

**Phase 1 gate:** T01–T06a all `DONE`, and T06b's verdict committed as PASS.
T07/T11/T16 intentionally depend on **T06a** (the evidence exists), not on T06b
(the human verdict), so work continues while the report awaits sign-off. If T06b
later returns FAIL, revisit anything that landed in that window.

### Track B — Structural hygiene (cheap, unblocks Phase 3)

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T07 | [Bound trace growth (per-player cap)](tasks/T07-trace-cap.md) | T06a | `BLOCKED` |
| T08 | [Distance-based self-neck immunity](tasks/T08-neck-distance.md) | T07 | `BLOCKED` |
| T09 | [Persist ER geometry across `drawArcs()` redraws](tasks/T09-er-persistence.md) | — | `READY` |
| T10 | [Dev hotkey alignment + on-screen legend](tasks/T10-dev-hotkeys.md) | T04 | `BLOCKED` |

### Track C — Phase 3 content (generation-gated)

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T11 | [Generation counter infrastructure](tasks/T11-generation-counter.md) | T06a | `BLOCKED` |
| T12 | [Gen 2 — membrane calcification](tasks/T12-gen2-calcification.md) | T11 | `BLOCKED` |
| T13 | [Gen 2 — organelle necrosis (lethal static walls)](tasks/T13-gen2-necrosis.md) | T11 | `BLOCKED` |
| T14 | [Gen 3 — the malignant mass](tasks/T14-gen3-malignant-mass.md) | T11 | `BLOCKED` |
| T15 | [Gen 4 — angiogenesis gravity well](tasks/T15-gen4-angiogenesis.md) | T11 | `BLOCKED` |

### Track D — Phase 4 juice

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T16 | [Camera screenshake utility](tasks/T16-screenshake.md) | T06a | `BLOCKED` |
| T17 | [Particle emitter splash system](tasks/T17-particles.md) | T16 | `BLOCKED` |
| T18 | [Warning-window post-processing filter](tasks/T18-warning-filter.md) | T16 | `BLOCKED` |

### Track E — Phase 5 UX

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T19 | [Quick Play button](tasks/T19-quick-play.md) | T03 | `READY` |
| T20 | [Control-mapping splash screen](tasks/T20-control-splash.md) | — | `READY` |

### Track F — Phase 2.2 (renderer-independent)

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T21 | [Extend additive blending on the vector renderer](tasks/T21-additive-blending.md) | — | `READY` |

### Track G — Architecture (enables Phase 7, speeds up testing)

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T22 | [Separate simulation from rendering](tasks/T22-sim-render-split.md) ⏳ *resumable* | T06a | `BLOCKED` |

### Track H — Phase 6: Mobile

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T23 | [Viewport, touch input, orientation](tasks/T23-mobile-viewport-touch.md) | — | `READY` |
| T24 | [Touch-friendly menu and HUD](tasks/T24-touch-ui.md) | T23 | `BLOCKED` |
| T25 | [Incremental trace rendering](tasks/T25-trace-render-perf.md) | T24 | `BLOCKED` |
| T26 | [Graphics quality tiers](tasks/T26-quality-tier.md) | T25 | `BLOCKED` |
| T27 | [Installable PWA (offline, home screen)](tasks/T27-pwa.md) | T26 | `BLOCKED` |

### Track I — Phase 7: Multiplayer

| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| T28 | [Fixed-timestep simulation](tasks/T28-fixed-timestep.md) | T22 | `BLOCKED` |
| T29 | [Network transport and lobby](tasks/T29-net-transport-lobby.md) | T28 | `BLOCKED` |
| T30 | [Host-authoritative state sync](tasks/T30-host-authoritative-sync.md) | T29 | `BLOCKED` |
| T31 | [Client prediction and interpolation](tasks/T31-client-prediction.md) | T30 | `BLOCKED` |
| T32 | [Network resilience and disconnects](tasks/T32-net-resilience.md) | T31 | `BLOCKED` |

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
