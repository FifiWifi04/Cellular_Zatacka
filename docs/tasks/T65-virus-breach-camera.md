# T65 — The virus breach still snapped the camera the instant control returned

**Track:** J · **Depends on:** T60 · **Risk:** medium (freeze/camera timing) · **Est. diff:** ~50 lines

Owner report, 2026-08-14: *"camera indeed slowed down during the virus release
but then after it happens it moves directly to the player and starts directly
without the chance for the player to adjust to zoom changes."*

Exactly right, and it is the defect T60 fixed for mitosis and explicitly decided
not to fix here.

---

## Cause

T60 gave mitosis a three-phase tail — **hold → zoomback → countdown** — where
the camera's target changes back to normal *while the freeze is still on*, and
the countdown only starts once the camera has arrived. Infection got the
countdown but not the zoomback, on this reasoning, written into the code:

> *"the camera target never changes across the breach (still centred on
> activeCell at the fixed viewSpan below), so there is no zoomback sub-phase to
> wait for here"*

**That is wrong.** The target does change — just later. `isVirus` was
`infection.state === 'warning'`, and the emergency framing is gated on `isVirus`,
so the wide shot held through the *entire* countdown. Only when the countdown
ended and `state` flipped to `'none'` did `isEmergency` go false and the camera
fall through to the follow branch — and by then the freeze had lifted and the
player was steering. The countdown ran on a shot the player was about to lose.

So the player got a 3-2-1 over the wide view, then the camera flew to them and
zoomed in with the round already live. Precisely the report.

### The second defect, found while fixing the first

Releasing the camera at the breach was not enough. `cameraAtTarget` is **one
render-step stale** — `updateCamera()` runs after this code — so on the release
frame it still reported "arrived" for the *wide* framing being left behind. The
settle gate passed immediately and the countdown started before the camera had
moved at all: measured **0.30 of zoom still travelling after control returned**,
on a 1280×1024 viewport.

Mitosis' `hold → zoomback` transition has the identical exposure. It happened to
measure well, but only by luck of frame ordering.

## Fix

1. `infection.cameraReleased`, set at the breach. `isVirus` becomes
   `infection.state === 'warning' && !infection.cameraReleased`, so the wide shot
   ends at the breach and the camera travels back **during** the freeze — the
   direct analogue of `isMitosisWideReveal = revealPhase === 'hold'`.
2. The countdown does not start until `cameraAtTarget`, with
   `MITOSIS_REVEAL_SETTLE_TIMEOUT` as the safety cap, mirroring mitosis.
3. **`cameraAtTarget = false` at both transitions** — the infection breach *and*
   mitosis' `hold → zoomback` — so the gate can never read a settle flag that
   describes the framing being abandoned.
4. The mitosis snap's `infection.state = 'none'` now clears the whole event, not
   just `.state`. It can land mid-breach, and a latched `breached` +
   `countdownEndsAt` would make the **next** warning see an already-expired
   countdown on its first frame and end itself instantly. T60's `breached` latch
   already had that exposure; it gained two more fields here, so it is closed.

## Verification

Forced warning (`infection.nextWarningTime = survivalTime`), 1 human + 3 bots,
godMode, sampling every rendered frame:

| | 640×480 (8.7 fps) | 1280×1024 (3.7 fps) |
|---|---|---|
| zoom travelled **while still frozen** | 0.272 | 0.355 |
| frozen seconds after camera release | 4.40 | 4.41 |
| breach → control returns | 4.32 game-s | 4.33 game-s |
| countdown digits seen | 3, 2, 1 | 3, 2, 1 |
| deaths during the freeze | **0** | **0** |
| zoom change after control returns | **0.0** | see below |

The 640×480 case is exactly flat. The 1280×1024 residual is the follow camera
tracking the bots spreading out once play resumes, not a settle tail — it ramps
in step with the players' bounding box rather than jumping and flattening:

| after control returns | zoom change | player bounding-box change |
|---|---|---|
| +0.25s | 0.010 | 45px |
| +0.5s | 0.023 | 88px |
| +1.0s | 0.049 | 175px |
| +2.0s | 0.057 | 212px |

Before the staleness fix (step 3) the same viewport showed 0.30 of zoom change
immediately after return, so the two are distinguishable and this is the good one.

Frozen-after-release is 4.40s vs 4.41s across a 2.4× frame-rate difference —
the settle wait plus the countdown are both frame-rate independent, as T60
required. `node --check` passes; console and page-error listeners empty.

## Definition of done

- [x] Camera released at the breach, travels back while frozen
- [x] Countdown gated on camera settle, with the timeout cap
- [x] `cameraAtTarget` invalidated at both transitions (infection **and** mitosis)
- [x] Mitosis snap clears the full infection event, not just `.state`
- [x] Zoom change after control returns ≈0; residual shown to be follow-tracking
- [x] Zero deaths during the freeze at both frame rates
- [x] `docs/TASKS.md`: T65 → `DONE`
