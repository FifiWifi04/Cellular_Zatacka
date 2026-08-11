# T54 — Persist runs and show a high-score table

**Track:** L (Phase 8) · **Depends on:** T53 · **Risk:** low-medium (first persisted state) · **Est. diff:** ~120 lines

Read [`docs/PHASE8-META-PROGRESSION.md`](../PHASE8-META-PROGRESSION.md).

T53 produces a score and a stats card that vanish when the round ends. This makes
them stick, and gives the owner the thing actually asked for: *"players can see
their high-scores with different statistics."*

---

## Design

### 1. Storage

`localStorage`, one key, JSON, **with a schema version from the first commit**:

```json
{ "v": 1, "runs": [ { "score": 0, "time": 0, "gen": 1, "stats": {…}, "at": 0, "mode": "…" } ], "totals": {…} }
```

- **Cap the history** (`HISTORY_MAX`, e.g. 50 runs). Unbounded growth in
  `localStorage` will eventually throw, and it throws on write — mid-game.
- **Every access must be wrapped.** Private browsing, a disabled-storage policy
  and a full quota all throw on read *or* write. A failure must degrade to
  "no history this session" and the game must play normally. Test it by stubbing
  `localStorage.setItem` to throw — do not assume.
- **Unknown/newer `v` → ignore and start fresh**, never crash and never silently
  reinterpret another version's shape.
- Corrupt JSON → same. Wrap `JSON.parse` in try/catch.

### 2. What the table shows

Top N by score, plus lifetime totals (rounds played, best generation reached,
total vesicles, total breaks, longest survival). Both the per-run *and* the
aggregate view — the owner asked for "different statistics", not one number.

Records should be per **mode** where it matters: a Quick Play 1v1 and a 4-player
round are not comparable. Store `mode` per run and either filter or label.

### 3. Where it lives

A panel reached from the main menu, built the same way as T41's help overlay —
which already solves the layout, the close button, the outside-click close, and
(after T46) the pause interaction. **Reuse that structure**; do not invent a
third overlay pattern.

A new high score should be called out on the end-of-round card. That moment is
the payoff.

### 4. Clearing

The player must be able to wipe their history, with a confirmation step. It is
their data on their device; do not make it unclearable.

## Verification

1. Console clean.
2. A completed run appears in the table; reload the page and it is still there.
3. **Storage failure is survivable** — stub `setItem` to throw, play a full
   round, confirm the game does not break and the failure is not spammed to the
   console every frame.
4. **Corrupt data is survivable** — write garbage into the key, reload, confirm a
   clean start rather than a crash.
5. **Wrong version is survivable** — write `{"v":99}`, reload, same.
6. `HISTORY_MAX` holds: play/simulate more runs than the cap, confirm the oldest
   drop and the payload stays bounded. State the stored byte size.
7. Table renders at 390×844, 844×390 and 1280×800; screenshot each.
8. Clearing works, and asks first.
9. New-high-score callout fires exactly when the score is a new best, and not
   otherwise.
10. Regression sweep §7.6.

## Definition of done

- [x] Versioned, capped, wrapped `localStorage` persistence
- [x] Per-run table **and** lifetime totals, mode-aware
- [x] Reuses the T41 overlay structure
- [x] All three failure modes (throw, corrupt, wrong version) proven survivable
- [x] Clear-history with confirmation
- [x] `docs/TASKS.md`: T54 → `DONE`, T55 → `READY`

---

## Findings

**Schema** (`localStorage['cellularZatackaHighScores']`, versioned):
```json
{ "v": 1,
  "runs": [ { "score": 810, "time": 3.6, "gen": 2,
              "stats": { "vesicles": {"membrane":3,"lysosome":0,"mitochondria":0},
                         "clusterBreaks":0, "massBreaks":0, "mitosisEvents":0, "distance":797 },
              "mode": "1h3ai", "at": 1786452777205 } ],
  "totals": { "rounds": 1, "bestGeneration": 2, "vesicles": 3, "breaks": 0, "longestSurvival": 3.6 } }
```
`mode` is human/bot composition (`"1h3ai"` = 1 human + 3 AI), not just player
count, per the task's "not comparable" note. `totals` is accumulated
independently of the capped `runs` array (incremented in `recordRun()` before
the cap is applied), so lifetime figures stay true lifetime even once old runs
age out of the 50-run history -- a design deliberately more literal than
"derive totals from the stored runs," which would have silently truncated
lifetime stats to whatever's left after `HISTORY_MAX`.

**Only human players are recorded** (`recordRunsForRoundEnd()` skips
`p.isBot`) -- it's the human's high-score table, not a leaderboard of the AI,
matching T53's "bots get the same stats object" without extending that to
persistence, which has no equivalent meaning for a bot. Recording happens once
per round end, at the same two `stepSimulation()` sites that already call
`renderStatsCard()`. Both sit behind the existing `fuzzActive` early-return
(`setTimeout(startRound, 0); return { ended: true };`), which returns before
the new `recordRunsForRoundEnd()` call is reached -- so fuzzer bursts, which
restart hundreds of rounds a minute, never write to the real history. This is
by inspection of the existing early-return, not a fuzzer run -- this task adds
no hazard, so §7.6's own fuzzer-adjacent sweep is out of scope (see below).

**Failure modes, each induced directly and confirmed survivable:**
- Corrupt JSON (`localStorage.setItem(KEY, 'not json{{{')`) -> `loadHighScores()`
  returns fresh data, no throw.
- Wrong version (`{v:99, runs:[...], totals:{}}`) -> same, ignored and fresh.
- `localStorage.setItem` stubbed to throw `QuotaExceededError` -> a full round
  still completes, `isPlaying` goes false, the stats card still renders, and
  the console stayed clean (the catch path uses `console.warn`, which the
  harness's error-only listener doesn't count, and it only fires once per
  round end since `saveHighScores()` is called nowhere in the per-frame path
  -- not spammed).

**`HISTORY_MAX` (50) holds**: pushed 60 synthetic runs, cap left exactly the
newest 50 (oldest kept run was `score: 10`, i.e. entries `0..9` dropped).
Stored payload size at the cap: **9,252 bytes** for 50 runs with realistic
per-run stats.

**New-high-score callout** (`p.isNewHighScore`, set by `recordRunsForRoundEnd()`
and read once by `renderStatsCard()`) fires exactly on a new best and not
otherwise: a run scoring 4 against a seeded prior best of 100 for the same
mode did **not** show "New Best!"; a subsequent run scoring 4005 against that
same prior best **did**. A mode's first-ever run also counts as a new best
(`priorBest` starts at -1), confirmed separately (first recorded run, score
810, showed the callout).

**Panel** reuses T41's help-overlay structure exactly (same `.help-overlay`/
`.help-panel`/`.help-close-btn` CSS, same outside-click-close, same
pause-on-open/resume-on-close via `highScoreIsOpen()` wired into the same
three call sites `helpIsOpen()` already was: the Escape/P handler, the `#ui`
mouseleave peek, and the outside-`pointerdown` resume). Screenshotted legible
at 390x844, 844x390 and 1280x800 (`/tmp/verify/t54_panel_*.png`) -- all three
scroll within the existing `.help-panel` `max-height: 90dvh` clamp, matching
how the Help panel already behaves at those sizes. Top-10-by-score table
confirmed rendering exactly 10 rows against a 12-run synthetic dataset.

**Clearing** asks first via `confirm()`: declining (`window.confirm` stubbed to
return `false`) left a 50-run history untouched; accepting (`true`) wiped it
to fresh `{runs:[], totals:{...zeroed}}`.

**Persistence across reload** confirmed on the same page (`page.reload()`,
`http://` origin): a recorded run and its totals were byte-identical before
and after.

**Offline (`file://`) load** confirmed clean: a full round played, ended, and
recorded a run under `file://`, with console and page-error listeners both
empty throughout.

**§7.6 regression sweep**: not applicable -- this task never touches
`checkCollision()`, `checkArcCollision()`, `raycast()` or
`rebuildSpatialGrid()` (confirmed via `git diff` grep), and adds no hazard.

`sw.js` `CACHE_NAME` bumped v31->v32; `dist/` rebuilt (`--check` passes).
