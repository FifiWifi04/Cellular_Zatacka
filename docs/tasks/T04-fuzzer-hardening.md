# T04 — Separate god mode from the fuzzer; harden the fuzzer

**Track:** A (Phase 1 gate) · **Depends on:** — · **Risk:** low · **Est. diff:** ~120 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Split the overloaded `devMode` flag into independent capabilities, and make the
fuzzer actually do what roadmap 1.2 specifies: **spawn maximum hazards**, trigger
rapid state toggles, restart instantly, and surface leak/`undefined` evidence.

## Why

Today `devMode` does two unrelated jobs:

1. It disables **every** death check — search for `!devMode` in `gameLoop` and you
   will find it guarding trace/organelle collision, microtubules, virus contact,
   and the sweep ring.
2. It gates the fuzzer (`if (devMode && (keys['f'] || keys['F']))`).

So **the fuzzer runs with all collisions disabled and can never detect a
collision bug**. It also cannot detect the round-restart path properly, because
players only die from causes that remain enabled. This defeats the purpose of
1.2, which exists to catch leaks and `undefined` crashes over long soak runs.

Additionally the current fuzzer only dilates time and forces the two big events.
It does not "spawn maximum hazards" as the roadmap requires.

---

## Prerequisites

Read: the `keydown` handler, the `// --- FUZZER SOAK-TEST UTILITY ---` block at
the top of `gameLoop`, every `!devMode` occurrence, `startRound()`,
`spawnVesicles()`, `updateInfection()`, and the `infection` and `mitosis` state
objects.

---

## Part 1 — Three independent flags

Replace the single `devMode` with:

```
let devMode    = false;   // master switch: enables the hotkeys + the HUD, nothing else
let godMode    = false;   // disables death checks
let fuzzActive = false;   // runs the soak loop
```

- Every existing `!devMode` guard in `gameLoop` becomes `!godMode`. There are
  five of them — find them all with a search for `devMode`, and check the one in
  the solo-game-over branch (`if (!players.some(p => p.alive) && !devMode)`)
  which should also become `godMode`.
- `devMode` now only gates the hotkeys and the on-screen indicator.

**`godMode` and `fuzzActive` must be independently settable.** The default fuzzer
run is `fuzzActive = true, godMode = false` — that is the configuration that can
actually find bugs.

## Part 2 — Hotkeys

Keep the existing toggle key(s) for `devMode`. Add, gated on `devMode`:

| Key | Action |
|---|---|
| `g` | toggle `godMode` |
| `f` | toggle `fuzzActive` (a **toggle**, not held — see below) |
| `Tab` | +15s `survivalTime` (unchanged) |

**Change `f` from held-to-active to a toggle.** A soak run must survive without a
human holding a key, and `run_test.py` currently fakes it with `keys['f'] = true`,
which is fragile. Update the indicator text to show which flags are on, e.g.
`⚙ DEV [god:on fuzz:off]`.

T10 aligns these with the roadmap's `\` and `]`; do not do that here.

## Part 3 — Maximum hazards

Inside the fuzzer block, when `fuzzActive`, drive the world to its stress limits.
Each of these must be **idempotent per frame** (do not spawn every frame — gate on
counts and timers):

1. **Vesicles at cap.** `updateVesicles()` caps at 25 with an 0.008/frame spawn
   chance gated on `window.golgiData`. While fuzzing, top up to the cap directly
   each second: if `vesicles.length < 25`, call `spawnVesicles()` for the
   difference at random valid positions.
2. **Virus swarm at maximum.** Force `infection` into its most populated state and
   keep `infection.particles` topped up. Read `updateInfection()` to find the
   natural maximum and use that number — do not invent a larger one that the rest
   of the code cannot handle.
3. **Mitosis on a tight cycle.** Already done via `mitosis.nextTriggerTime = 0.1`.
   Keep it.
4. **All four players alive as bots.** Optional but valuable: when `fuzzActive` is
   switched on, if fewer than 4 players exist, restart the round with
   `currentMode = 1, aiCount = 3`. This maximises trace count, which is the main
   driver of grid rebuild cost.
5. **Rapid state toggles.** Every ~0.5s of fuzz time, flip a random alive
   player's `targetMode` between `'self'` and `'attack'`, and toggle
   `cameraMode` between `'shared'` and `'split'`. The camera toggle is the one
   most likely to expose `splitSprites` / `RenderTexture` lifecycle bugs.

## Part 4 — Instrumentation

The fuzzer's output is the point. Add a `fuzzStats` object updated once per
second while `fuzzActive`, and render it into the existing `devIndicator` element
(plain text, no new PixiJS objects — do not add rendering cost to the thing you
are measuring):

```
fuzzStats = {
  rounds:        <int>,   // startRound() calls since fuzz began
  elapsed:       <sec>,   // wall-clock fuzz duration
  tracePoints:   <int>,   // sum of all traceSegments lengths
  gridCells:     <int>,   // spatialGrid.cells.size
  worldChildren: <int>,   // recursive display-object count under `world`
  vesicles, organelles, virusParticles: <int>,
  heapMB:        <number|null>,  // performance.memory.usedJSHeapSize/1048576
                                 // (Chrome only; show null elsewhere)
  errors:        <int>,   // see below
}
```

Add a global error trap **once**, near the top of the script:

```
window.addEventListener('error', e => { fuzzStats.errors++; console.error('[FUZZ]', e.message); });
window.addEventListener('unhandledrejection', e => { fuzzStats.errors++; });
```

`worldChildren` is the leak canary: write a small recursive counter over
`world.children`. In a healthy build it must be **flat across rounds**. If it
climbs every `startRound()`, that is the PixiJS lifecycle leak T05 fixes.

Also expose `window.fuzzStats` so a headless driver can read it without scraping
the DOM.

## Part 5 — Restart robustness

The current auto-restart is `if (aliveCount === 0) { startRound(); return; }`.
Two problems:

- With `godMode` off and 4 bots, rounds now genuinely end, so this path runs
  constantly — good, that is the point. Make sure `fuzzStats.rounds++` happens
  here.
- `startRound()` calls `app.ticker.start()` and the solo game-over branch calls
  `app.ticker.stop()`. Confirm by reading that a fuzz restart cannot leave the
  ticker stopped. If it can, restart from a `setTimeout(startRound, 0)` outside
  the tick instead of calling it inline.

---

## Files touched

`260703_Cellsnake.html` only: flag declarations, `keydown` handler, `devIndicator`
text, every `!devMode` guard in `gameLoop`, the fuzzer block, new `fuzzStats` +
error handlers.

Do not change any gameplay constant. Do not change `startRound()`'s behaviour.

---

## Verification

1. Console clean on load.
2. **Flags are independent.** `devMode` on, `godMode` off, `fuzzActive` off →
   you die normally. `godMode` on → you do not. `fuzzActive` on with `godMode`
   off → bots die and rounds cycle.
3. **The fuzzer can now detect collision.** With `fuzzActive` on and `godMode`
   off, confirm `fuzzStats.rounds` increments — proving deaths are being
   registered. Before this task it would have stayed at 0 forever.
4. **Hazards are maxed.** With fuzz on, observe `vesicles` at/near 25 and
   `virusParticles` at its documented maximum in the HUD.
5. **No new per-frame cost.** Confirm the HUD updates once per second, not per
   frame.
6. **10-minute smoke run.** Leave fuzz on for 10 minutes. `fuzzStats.errors`
   must be 0. Record `rounds`, `worldChildren` at start vs. end, and `heapMB` at
   start vs. end in the commit message — this is the input T06 builds on.
7. Update `run_test.py` to set `fuzzActive` via the new toggle rather than
   `keys['f'] = true`.

## Definition of done

- [ ] `devMode`, `godMode`, `fuzzActive` are three independent flags
- [ ] All five `!devMode` death guards now read `!godMode`
- [ ] `f` is a toggle, not held
- [ ] Hazard maximization implemented and idempotent per frame
- [ ] `window.fuzzStats` populated, including `worldChildren` and `errors`
- [ ] Global `error` / `unhandledrejection` traps installed
- [ ] 10-minute smoke run clean, numbers in commit message
- [ ] `run_test.py` updated
- [ ] `docs/TASKS.md`: T04 → `DONE`, T10 → `READY`; T06 → `READY` if T05 done
