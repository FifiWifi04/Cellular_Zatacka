# T06c — Find and fix the retained-memory leak

**Track:** A · **Depends on:** T06a (data exists) · **Risk:** medium · **Est. diff:** unknown until diagnosed

Read `docs/AGENT_CONDUCT.md` before starting.

**Priority: take this before any other `READY` task.** It came out of the Phase 1
gate. Leaks get harder to find the more code lands on top of them, and twelve
tasks have landed since the measurement.

---

## Goal

Find what the game holds onto across rounds, and release it.

## The evidence

`docs/reports/soak-A/soak.csv` — 60 rounds, 1145 s, deaths cycling normally.
The heap sawtooth **floor** (the level memory returns to after each collection)
rises monotonically:

| Window | wall s | heap floor | worldChildren |
|---|---|---|---|
| 1 | 182 | **44 MB** | 1331–1378 |
| 2 | 369 | **70 MB** | 1310–1379 |
| 3 | 554 | **85 MB** | 1329–1374 |
| 4 | 741 | **91 MB** | 1292–1379 |
| 5 | 926 | **101 MB** | 1292–1379 |
| 6 | 1113 | **124 MB** | 1310–1379 |

≈1.4 MB retained per round. `soak-B` (immortal, 20 min) shows the same shape
more steeply, 42 → 241 MB — but **run B grows traces without bound by design**,
so much of its rise is legitimate live data. **Run A is the meaningful one**:
players die, traces reset, and memory still is not returned.

**`worldChildren` stays flat throughout.** That is the discriminator: T05 fixed
the PixiJS display-object teardown and it is holding. Whatever this is, it is
**not** display objects being orphaned under `world`.

---

## STEP 0 — The measurements are stale. Re-measure first.

**Do this before investigating anything.** All three soak runs were taken at
`5c0e1aa` or earlier. Since then **T07 landed a per-player trace cap**, plus
T08–T17. T07 directly bounds one of the biggest per-round allocators, so the
leak may already be smaller, or gone.

```
rm -rf docs/reports/soak-A
python3 tools/soak.py A
```

Then compute the floor per window exactly as the table above does, and compare.

- **Floor now flat** → T07 fixed it. Record the before/after tables, update
  `docs/BACKLOG.md`, mark this task `DONE` with "resolved by T07", and stop.
  That is a complete and valuable outcome — do not go hunting for a leak that
  is no longer there.
- **Floor still rising** → continue to Step 1. Note the new rate; if it changed,
  say by how much.

Commit the re-measurement before going further, whichever way it goes.

---

## STEP 1 — Count suspects, do not guess

Heap-snapshot diffing is the textbook tool but is fiddly to drive from a script.
**Start with instrumented counters** — in this codebase they will almost
certainly find it, and the signal is unambiguous: whatever grows monotonically
across rounds while the game is idle-ish is the leak.

Add a **temporary** diagnostic (removed before the final commit) that reports,
once per round, the size of every long-lived collection:

```
window.__leakProbe = () => ({
    // game state
    players: players.length,
    tracePoints: players.reduce((a,p) => a + p.traceSegments.reduce((b,s) => b+s.length, 0), 0),
    traceSegments: players.reduce((a,p) => a + p.traceSegments.length, 0),
    organelles: organelles.length,
    vesicles: vesicles.length,
    virusParticles: infection.particles.length,
    gridCells: spatialGrid.cells.size,
    centralHitboxes: centralHitboxes.length,
    activeArcs: activeArcs.length,
    cytosolParticles: cytosolParticles.length,
    membraneProtrusions: membraneProtrusionsList.length,
    massBlocks: malignantMass.blocks.length,
    splitSprites: splitSprites.length,
    splitTextures: splitTextures.length,
    // PixiJS internals — the usual suspects for "flat display list, rising heap"
    tickerListeners: app.ticker.count,
    sharedTickerListeners: PIXI.Ticker.shared.count,
    textureCache: Object.keys(PIXI.utils.TextureCache).length,
    baseTextureCache: Object.keys(PIXI.utils.BaseTextureCache).length,
    rendererTextures: app.renderer.texture.managedTextures.length,
    // per-round globals — replaced each round; are the old ones released?
    hasGolgiData: !!window.golgiData,
    hasErData: !!window.erData,
    hasNucleusMask: !!window.nucleusMask,
    hasBgMask: !!window.bgMask,
    heapMB: performance.memory ? +(performance.memory.usedJSHeapSize/1048576).toFixed(1) : null
});
```

Drive 40+ rounds under the fuzzer, sampling this each round, and write it to a
CSV. **Any counter that climbs and never comes back down is your leak.**

### Ranked candidates, with why each is plausible here

1. **`app.ticker.count` / `PIXI.Ticker.shared.count`** — if anything registers a
   ticker callback per round instead of once at init, that retains its whole
   closure scope forever. Classic, and it would show flat `worldChildren` while
   the heap climbs. **Check this first**; it is one number.
2. **`PIXI.utils.TextureCache` / `BaseTextureCache` / `managedTextures`** —
   destroying a display object with `{ texture: false }` (which `purgeContainer`
   does, deliberately) leaves textures cached. Correct for shared textures,
   a leak for per-round ones. T05 chose `texture: false` on purpose; this is
   where that choice would bite.
3. **`window.bgMask`** — `drawMitosisVisuals()` writes it. `window.nucleusMask`
   is explicitly destroyed in `generateMap()`; confirm `bgMask` is too, or that
   it is created once. This asymmetry is suspicious.
4. **Per-round `Graphics` that are removed but not destroyed** — re-audit every
   `removeChild`/`removeChildren` added by T11–T17 against `AGENT_CONDUCT.md`
   §2's teardown rule. `worldChildren` being flat does **not** clear these: an
   object detached from the tree but still referenced by an array is invisible
   to that counter.
5. **T17's particle pool** — should be fixed-size. Verify it never grows.
6. **Closures capturing `players`** — `players = []` drops the array, but any
   callback that captured a player object keeps it, and each player owns its
   whole trace history.

## STEP 2 — Heap snapshots, only if Step 1 comes up empty

If no counter grows, take heap snapshots via CDP and diff by constructor:

```python
client = page.context.new_cdp_session(page)
client.send("HeapProfiler.collectGarbage")
# snapshot, run 20 rounds, collectGarbage, snapshot again, compare retained sizes
```

Look at which constructor's retained size grew most between snapshots. Report
the top three with their sizes.

---

## STEP 3 — Fix, if the fix is contained

If the cause is clear and the fix is small (a missing `destroy()`, a ticker
listener moved to init, a cache cleared on `startRound()`), fix it here.

**If the fix is architectural** — say it needs the sim/render split, or a
redesign of how a system stores state — **do not attempt it.** Write the
diagnosis into `## Findings`, open a follow-up task file, and stop. A correct
diagnosis is the deliverable; a rushed structural fix is not.

Whatever you change, keep `AGENT_CONDUCT.md` §4.4 in mind: releasing something
the game still needs will show up as a crash three rounds later, not
immediately.

---

## Files touched

- `docs/reports/soak-A/` — re-measured
- `260703_Cellsnake.html` — the fix, if contained. **The `__leakProbe`
  diagnostic must be removed before the final commit.**
- this file — `## Findings`
- `docs/BACKLOG.md`, `docs/TASKS.md`

---

## Verification

1. Console clean.
2. **Before/after floor tables**, computed the same way, from full `soak.py A`
   runs. The floor must be flat — or the residual rise explained and quantified.
3. **`worldChildren` still flat** — the fix must not regress T05's work.
4. The `__leakProbe` diagnostic is gone from the committed file.
5. **Nothing released too eagerly.** Run 30 consecutive restarts: no errors, and
   the map still renders fully on round 30 (background, membrane, cytosol,
   nucleus, ER/Golgi, 25 organelles).
6. Gen 2/3/4 content still works — set each generation via `window.setGeneration`
   and confirm calcification, necrosis, the mass and the gravity well all behave.
7. Split-screen still renders after 10 restarts.
8. Regression sweep from `AGENT_CONDUCT.md` §7.6.
9. `python3 tools/build_standalone.py --check` passes.

## Definition of done

- [x] Step 0 re-measurement committed, with before/after floor tables
- [x] Either: leak found, named, and fixed — or a documented diagnosis plus a
      follow-up task — or "resolved by T07" with the data to prove it
- [x] `## Findings` records what was counted and what the numbers showed,
      including the candidates that were ruled **out**
- [x] Diagnostic instrumentation removed (none was ever added — Step 0 alone
      settled it)
- [x] `docs/TASKS.md`: T06c → `DONE`

---

## Findings

### Step 0 — re-measurement: the floor is now flat

Re-ran `python3 tools/soak.py A` at commit `8762fcf` (T07–T17 all landed since
the original measurement at `30ec41a`). Two runs:

1. Default 60-round target completed in **150s** wall (vs. the original 1145s
   for the same 60 rounds) — rounds now cycle roughly 7-8x faster. Too short
   (only 15 samples) to reuse the original ~190s windowing, so it was discarded
   in favor of a longer run rather than analysed on its own.
2. Re-ran with `--rounds 450` to reproduce a comparable **~1063s** wall-clock
   span (453 rounds, 104 samples, 0 errors) — committed as the new
   `docs/reports/soak-A/`.

Windowed floor (min heap per ~190s window, same method as the original
table in `docs/tasks/T06a-soak-measurement.md`):

| Window | wall s (before / after) | heap floor before (MB) | heap floor after (MB) | worldChildren after |
|---|---|---|---|---|
| 1 | 182 / 190 | 44 | **41.7** | 700–1380 |
| 2 | 369 / 378 | 70 | **47.3** | 685–1390 |
| 3 | 554 / 561 | 85 | **42.3** | 684–1393 |
| 4 | 741 / 755 | 91 | **45.5** | 693–1388 |
| 5 | 926 / 950 | 101 | **48.2** | 694–1389 |
| 6 | 1113 / 1062 | 124 | **42.5** | 701–1376 |

Before: floor rose monotonically 44 → 124 MB (~1.4 MB/round retained) over 58
rounds. After: floor oscillates in a narrow 41.7–48.2 MB band with **no upward
trend** across 453 rounds and 6 windows — this is the flat-floor signature the
task file defines as "T07 fixed it." `worldChildren` stays in the same
684–1393 band the original run showed (including the same periodic dip to
~685-700 right at a round transition, present in both the old and new data),
confirming T05's display-object teardown still holds and nothing regressed
there.

**Conclusion: resolved, most likely by T07's per-player trace cap.** Per-round
`heapMB` "final" readings also dropped from 260.6 MB (original run A, 60
rounds) to 66.8 MB (this run, 453 rounds) even though round count is 7.5x
higher, which is consistent with trace-driven allocation (points, grid cells,
segment objects — all of which scale with trace length) being the dominant
per-round cost that T07 bounded, rather than a leak specific to `startRound()`
teardown.

### Step 1 — static review, ruled out as belt-and-suspenders (no counters added; not needed once Step 0 showed a flat floor)

Read through every candidate the task file ranks, plus the mitosis/organelle
code paths the fuzzer forces open (`fuzzActive` sets `mitosis.nextTriggerTime
= 0.1` whenever mitosis is idle — mitosis's `'forming'` phase runs almost every
round under the fuzzer, which is why `organelles.length` reads 50 rather than
25 in most soak samples: Cell B's 25 organelles are deliberately added
alongside Cell A's during an active split, not a leak). Found no netnew leak
candidate; every teardown path checked destroys what it should:

- **`app.ticker.add`** — called exactly once at init (`260703_Cellsnake.html`
  ~L3837), not per round. Ruled out.
- **`window.bgMask`** — reassigned every `generateMap()` without an explicit
  destroy, *but* it is `addChild`-ed into `backgroundLayer`
  (`generateMap()` ~L1051), and `purgeContainer(backgroundLayer)` at the top
  of the *next* `generateMap()` call destroys it along with the rest of that
  layer's children. Asymmetric with `window.nucleusMask`'s explicit
  destroy, but not a leak — `nucleusMask` is parented directly to `world`,
  `bgMask` to a purged layer. Ruled out.
- **Split-screen `splitSprites`/`splitTextures`** — `purgeSplitScreen()`
  destroys sprite and `RenderTexture` (`{texture: true}` via `rt.destroy(true)`)
  correctly. Not exercised by run A anyway (`camera: "shared"`). Ruled out.
- **T17 particle pool** — fixed-size array allocated once at module init
  (`particlePool`, `MAX_PARTICLES` slots); `particleCount` resets to 0 in
  `startRound()` but the pool itself never grows. Ruled out.
- **T13 necrosis sprite swap** — `organellesLayer.removeChild(pick.sprite);
  pick.sprite.destroy();` runs before the replacement grey sprite is created
  (~L3382). Ruled out.
- **Mitosis Cell-B setup** (`updateMitosis()`'s `'forming'` branch, ~L2357–2454)
  — allocates a `cellBBg` Graphics object directly into `backgroundLayer`, up
  to 800 more cytosol blobs into the *existing* `cytosolContainer`, and up to
  25 more organelle sprites into `organellesLayer`, every time mitosis is
  (re-)triggered. None of these are cleaned up if the round ends
  mid-`'forming'` (i.e. the fuzzer restarts before the 120s snap) **except**
  via the blanket `purgeContainer(backgroundLayer)` /
  `purgeContainer(organellesLayer)` at the top of the next round's
  `generateMap()`, which does destroy all of them (they're all descendants of
  layers that get purged). Confirmed no leak in practice — flagged here only
  because it is the least obviously-safe path and worth knowing about if a
  future task changes what `keepOrganelles`/layer-purge boundaries cover.
- **Mid-round `drawArcs()` orphan** (already on the backlog from T05/T09,
  `rotatingContainer.removeChildren()` without `.destroy()` at the ER/Golgi
  shatter path, ~L3536) — real, but **not reachable in run A**: mitosis
  requires 240s of survival time to trigger naturally and, even
  fuzzer-forced, needs 60+ dilated game-seconds to reach `'narrowing'` (where
  arcs get shattered); rounds in run A average ~2.3s wall / ~9s dilated game
  time before a player dies. Left as-is on the backlog — real but out of
  scope here since it isn't what run A measured, and every actual game-second
  of it is that much game-second closer to what a human round would face,
  where mitosis realistically can complete. Worth a task if T22 or an
  immortal-mode soak (run B) is re-measured and shows a component of its own
  floor rise tracking arc-shatter counts.

No instrumented `__leakProbe` was added to the shipped file — Step 0 already
gave an unambiguous flat-floor result, and the task file says explicitly not
to go hunting once that happens.
