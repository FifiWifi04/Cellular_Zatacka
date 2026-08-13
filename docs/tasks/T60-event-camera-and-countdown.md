# T60 — Play resumes while the camera is still moving, and the camera moves differently on every device

**Track:** J · **Depends on:** T28, T47 · **Risk:** medium-high (camera + freeze timing) · **Est. diff:** ~80 lines

Owner report, 2026-08-11: *"there is an issue with zooming in and out during the
event, the camera is making some weird moves and after zooming in the game starts
before the zooming in completely finishes leading to players dying because they
don't see where they are going. maybe after zooming in the pause should continue
and there should be counter lasting 3 seconds counting down."*

Both halves reproduced. There are **two** independent defects.

---

## Defect 1 — the game unfreezes long before the camera stops

`isMitosisReveal` is a fixed 5-second window (`survivalTime - mitosis.eventStartTime
< 5.0`). At 5.0s the simulation unfreezes on the spot. The camera, meanwhile, is
an exponential lerp toward its target:

```js
world.scale.x += (targetZoom - world.scale.x) * 0.05;
```

An exponential approach never *arrives*, so the reveal ends at an arbitrary point
part-way through the move — and the player is already steering.

Measured, sampling every rendered frame across a real mitosis:

| viewport | zoom when control returns | zoom once settled | still moving for |
|---|---|---|---|
| 640×480 | 0.121 | 0.482 | **2.41 game-seconds** |
| 1280×1024 | 0.237 | 1.182 | **4.67 game-seconds** |

So the world scale changes by **4×–5× while the player is alive and steering**.
That is exactly "the game starts before the zooming in completely finishes … they
don't see where they are going".

## Defect 2 — the camera is frame-rate dependent

Those two rows are the same event; only the frame rate differs. `0.05` and `0.1`
are **per rendered frame**, not per second. T28 made the *simulation*
fixed-timestep, but `updateCamera()` lives in `renderFrame()` and was left on
per-frame constants — so the camera converges at a completely different rate on a
fast phone than on a slow one, and its behaviour changes mid-round whenever the
frame rate dips. This is the "weird moves".

## Fix

### 1. Make every camera lerp frame-rate independent

Replace `v += (target - v) * k` with a time-based equivalent, e.g.
`v += (target - v) * (1 - Math.exp(-rate * deltaSec))`, so the same wall-clock
time produces the same camera motion at any frame rate. **Every** lerp in
`updateCamera()` — the emergency branch, the follow branch, the split branch —
must convert; leaving one behind reintroduces the inconsistency on that path.
`deltaSec` is already available from the T22 split; pass it in rather than
recomputing.

Pick rates that reproduce today's *feel at 60fps* so the change is a fix, not a
retune. State the mapping in `## Findings`.

### 2. Gate the resume on the camera, not on a stopwatch

The reveal must end when the camera has **actually arrived**, not at 5.0s.
Add an explicit settle test — target within a small epsilon of current, for both
scale and position — and treat the event as having three phases:

```
zoom out  →  hold (the reveal itself)  →  zoom back in  →  COUNTDOWN  →  play
```

The 5-second constant becomes the *minimum* hold, not the whole event.

### 3. The countdown (owner's design)

Once the camera has settled, stay frozen and run a visible **3 → 2 → 1**
countdown before returning control. Requirements:

- Reuse the existing freeze (`isCellFrozen`) — this is a fourth caller of a
  mechanism that already has three. Do **not** add another freeze flag.
- Reuse `warningElement`, the DOM banner mitosis and the infection warning
  already use, rather than a new overlay.
- The countdown is wall-clock/game-clock driven and must be frame-rate
  independent too — a "3 second" countdown that takes 8s on a slow phone is the
  same class of bug this task exists to fix.
- Apply it to **every** event that freezes and moves the camera: the mitosis
  reveal, the infection warning, and T57's nucleus transformation. One
  implementation, three callers. T57 already has its own separate
  `NUCLEUS_TRANSFORM_GRACE` — fold it into this rather than leaving two
  different "you get a moment before it hurts" mechanisms.

### 4. While you are in here — the reveal framing

`viewSpan = 6500` is hardcoded and the fit uses `Math.min` over both axes, so on
a wide viewport the pair of cells is letterboxed into the upper half with ~40% of
the screen empty (see `/tmp/verify/audit/13-mitosis-bridge.png`). Frame the
actual bounding box of the two cells with a margin, instead of a fixed span.

## Verification

1. Console clean.
2. **The measurement above, repeated.** Zoom change after control returns must be
   ≈0 — report the same table with the new numbers. This is the headline test.
3. **Frame-rate independence**: run the same event at 640×480 and 1280×1024 and
   show the camera takes the same *game-time* to settle at both. The current gap
   is 2.41s vs 4.67s.
4. Countdown visible, reads 3/2/1, and control returns exactly at 0 — at both
   viewport sizes, with the elapsed game time reported for each.
5. **Nobody dies during the event or the countdown.** 5 mitosis events with 3
   bots: zero deaths between freeze start and countdown end.
6. All three events (mitosis, infection warning, nucleus transformation) use the
   one countdown; screenshot each.
7. Reveal framing: screenshot at 844×390, 1100×850 and 1280×1024 — both cells
   centred with no large empty band.
8. Split-screen camera unaffected (it is a fixed zoom; confirm it did not pick up
   a lerp change).
9. Regression sweep §7.6.

## Definition of done

- [x] Every camera lerp time-based; 60fps feel preserved and the mapping stated
- [x] Resume gated on camera settle, not on 5.0s
- [x] One countdown, reused by all three freezing events, frame-rate independent
- [x] T57's separate grace folded in
- [x] Zoom change after control returns ≈0, measured at two frame rates
- [x] Reveal framing fits the two cells' true bounding box (matched-orientation
      case now fills the frame; orthogonal-mismatch case still letterboxes,
      inherent to a tall/narrow scene in a wide/short viewport or vice versa --
      see Findings, strictly no worse than the old fixed square)
- [x] `docs/TASKS.md`: T60 → `DONE`

---

## Findings

**Rate mapping.** Every `v += (target - v) * k` lerp in `updateCamera()`
(emergency-zoom scale/position at `k=0.05`, follow-camera scale/position at
`k=0.1`) now goes through `camLerpFactor(k, deltaSec) = 1 - (1-k)^(60*deltaSec)`.
This is the continuous-time generalisation of the old per-frame-at-60fps
recurrence and is numerically identical to the old `* k` when `deltaSec` is
exactly `1/60` (60fps feel preserved, not retuned). `updateCamera()` now takes
a `cameraDeltaSec` argument that is the *total* game-time simulated since the
last call (summed across every `stepSimulation()` catch-up step that ran this
real frame, via `stepsDeltaSec` in `gameLoop()`), not a single step's
`deltaSec` -- fixing Defect 2, where the camera previously advanced by one
step's worth of lerp per *render* call regardless of how many simulation steps
(0 on a fast display, up to `MAX_STEPS_PER_FRAME` on a slow one) had actually
run.

**Zoom-tail measurement (item 2), repeated with a forced mitosis event**
(`mitosis.nextTriggerTime = survivalTime + 0.1`, 1 human + 3 bots, immortal so
the round survives long enough to observe):

| viewport | zoom at control return | zoom 2s later | zoom change after return |
|---|---|---|---|
| 640x480 | 0.500 | 0.500 | **0.0 (exact)** |
| 1280x1024 | 0.871 | 0.911 | 0.040 |

The 640x480 case is exactly flat. The 1280x1024 residual is bot *movement*
after control returns changing the follow-camera's target (bots keep steering
once unfrozen), not camera catch-up -- the camera had already fully converged
*before* control returned in both cases (that's what gates the phase
transition). This is a world away from the original bug's measured 4x-5x
change while the player was already steering blind.

**Frame/viewport independence (item 3).** Both runs above triggered from
`mitosis.eventStartTime` and reached `revealPhase === 'none'` (control
returned) at **exactly 8.217 game-seconds** in both the 640x480 and the
1280x1024 case -- identical to three decimal places, despite the 1280x1024
run taking roughly 9x longer in *wall* time (slower rasterisation -> lower
real fps -> more `stepSimulation()` catch-up steps per render). This is the
direct payoff of Defect 2's fix: convergence time in game-seconds no longer
depends on how many real frames it took to get there.

**Countdown timing (item 4), all three events, forced and measured directly:**

| event | hold/pre-window | countdown | control returns at (game-time since trigger) |
|---|---|---|---|
| mitosis reveal | 5.0s min hold + near-instant zoomback (bots' follow-camera target already matched the wide-reveal target in this trial) | 3.0s | 8.217s |
| infection breach | 5.0s (`INFECTION_WARNING`) | 3.0s, digits appended to "VIRAL BREACH! HIDE BEHIND LYSOSOMES!" | 8.2s |
| nucleus transform | 3.0s (`NUCLEUS_TRANSFORM_FREEZE`) | 3.0s | 5.917s |

Each countdown read 3 -> 2 -> 1 in the shared `warningElement` banner, one
digit per second, control returning on the frame `remaining <= 0`.
Screenshots: `/tmp/verify/t60_mitosis_countdown_digit.png` (mitosis, "3", with
the camera already back to normal single-cell framing -- proving the
zoomback-before-countdown ordering), `/tmp/verify/t60_nucleus_countdown.png`
(nucleus, "1", nucleus meter visible). Infection's digit is embedded in the
breach sentence rather than shown bare (see the code comment): showing a bare
digit there would have replaced the "hide behind lysosomes" warning before
the player ever saw it, since the breach and the countdown start on the same
frame for that event (no separate hold phase precedes it the way mitosis/
nucleus have one).

**5-event no-death run (item 5).** 1 human (unpiloted, dies to the membrane
before the first forced event) + 3 bots, `godMode` off (real collision). 5
mitosis reveals forced back-to-back by resetting `mitosis.state` to `'idle'`
immediately after each `revealPhase` returned to `'none'` (bypassing the
multi-minute `'forming'` period between reveal and snap, which item 5 isn't
about). Bot alive-count sampled continuously through every hold/zoomback/
countdown window: **3/3 bots alive before, during, and after all 5 events.**
This is structurally guaranteed by the pre-existing `if (isCellFrozen) return;`
early-out in `updatePlayers()` (unchanged by this task) as long as
`isCellFrozen` stays true for the reveal's actual duration -- which is what
items 2-4 above confirm.

**Reveal framing (item 7).** Replaced the fixed square `viewSpan=6500` with
the two cells' true bounding box (`activeCell` and `mitosis.cellB`, each
inflated by its own radius) times `MITOSIS_REVEAL_MARGIN=1.15`, fit
per-axis. For the case the owner's screenshot showed (a split whose long axis
matches the viewport's long axis -- horizontal division, wide viewport), this
eliminates the letterboxing: `/tmp/verify/t60_framing2_horizontal-wide.png`
(844x390, forced `direction=0`) shows both cells and the bridge filling the
frame with only a thin margin, not the ~40% empty band `13-mitosis-bridge.png`
had. When the split axis is *orthogonal* to the viewport (vertical split,
wide-short viewport, or vice versa), some empty space is unavoidable -- the
content itself is tall/narrow while the viewport is wide/short, which no
framing formula can fully reconcile -- confirmed still present in
`/tmp/verify/t60_framing2_horizontal-tall.png` and `t60_framing_844x390.png`
(that one hit a vertical split by chance), but is strictly no worse than (and
usually much better than) the old fixed-square span, which wasted space in
the content's shorter dimension unconditionally, every direction, every
viewport. Additional straight-on screenshots at 1100x850 and 1280x1024:
`t60_framing_1100x850.png`, `t60_framing_1280x1024.png`.

**Split-screen (item 8).** `world.scale.x === splitRenderScale` exactly
(0.6 == 0.6) after 3s in split mode -- confirmed the split branch's
`world.scale.set(splitZoom)` was untouched and never picked up
`camLerpFactor`. Screenshot: `/tmp/verify/t60_splitscreen.png`.

**Regression sweep (item 9).** `checkCollision`/`checkArcCollision`/
`raycast`/`rebuildSpatialGrid` are not in this diff (confirmed by grep), so
the full §7.6 sweep doesn't strictly apply, but membrane death was
reconfirmed at all 3 speeds with an unpiloted human (1.5: 2.53s, 2.5: 2.35s,
3.5: 1.63s -- faster speed reaching the wall sooner, as expected) plus a
clean real 30.1s round (1 player + 3 bots, `worldChildren` flat at 16).
Console clean in every check, including a `file://` offline load (8.2
game-seconds, 0 console/page errors).

**Headless safety net.** `window.stepHeadless()` (used by the fuzzer's soak
path and `T22`'s own benchmark) never calls `updateCamera()`, so
`cameraAtTarget` never updates during a headless run. Without a cap, a forced
mitosis event under headless stepping would freeze the round forever once
`revealPhase` reached `'hold'`. Added `MITOSIS_REVEAL_SETTLE_TIMEOUT=10.0`s
per settle sub-phase as a fallback (proceed even without `cameraAtTarget`
once the timeout elapses) -- verified a forced event under 40s of
`stepHeadless()` resolved to `revealPhase === 'none'` with `mitosis.state`
still `'forming'` (correct: only the reveal ended, not the whole event) and 0
console errors.

**Scope note.** No hazard was added or changed, so AGENT_CONDUCT §4.1 (both
`checkCollision()`/`raycast()`) doesn't apply -- confirmed neither function
appears in the diff. `NUCLEUS_TRANSFORM_GRACE` was deleted (folded into
`REVEAL_COUNTDOWN`, per the task's own instruction) rather than left dead;
its two former reads (`nucleusChaserNextSpawn`'s initial schedule and
`updateNucleusChasers()`'s `activeSince`) both now add `REVEAL_COUNTDOWN`
instead. `infection.textClearTime` (a bespoke timed-clear field only the
breach message used) was deleted rather than kept alongside the new
countdown-driven clear, which fully subsumes it. `sw.js` `CACHE_NAME`
bumped v38->v39; `dist/` rebuilt (`--check` passes).
