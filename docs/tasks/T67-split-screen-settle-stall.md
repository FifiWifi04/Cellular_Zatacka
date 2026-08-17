# T67 — Split-screen stalls 10s before the countdown, and the digit lies while it waits

**Track:** J · **Depends on:** T65 · **Risk:** low · **Est. diff:** ~20 lines

Owner report, 2026-08-14: *"In a two player game with AI during the virus the
waiting time is much longer than 3 seconds. The game zoomes on to the player but
then freezess for few seconds before the actual countdown happens."*

Two causes, one structural and one cosmetic. Both were introduced by T65.

---

## Cause 1 — the split-screen branch never sets `cameraAtTarget`

T65 gates the countdown on `cameraAtTarget`, and clears it when the event
releases the camera so the gate cannot read a stale value.

`updateCamera()`'s **split-screen branch assigns `cameraAtTarget` nowhere.** It
snaps — `world.scale.set(splitZoom)`, `world.x = …` per viewport, no lerp
anywhere in that branch — so the flag was never needed there before.

Consequence: in split-screen the breach clears the flag to `false` and nothing
ever sets it back. The gate can only fall through to
`MITOSIS_REVEAL_SETTLE_TIMEOUT` — **a 10-second stall before the 3-second
countdown even starts**, ~13s total. This also applied to the mitosis reveal in
split-screen; it just had not been hit yet.

**Fix:** set `cameraAtTarget = true` at the end of the split branch. The split
camera is at its target by construction, every frame.

## Cause 2 — the banner showed a frozen "3" while the camera travelled

The settle wait printed `Math.ceil()` of a countdown that had not started:

```js
let remaining = infection.countdownEndsAt === -Infinity
    ? REVEAL_COUNTDOWN                       // <-- a constant 3
    : infection.countdownEndsAt - survivalTime;
```

So the player saw **"… 3"** sitting motionless for the whole camera move and only
then start ticking — which reads as the game having hung. In split-screen that
was a stuck "3" for ten seconds.

**Fix:** no digit until there is a real one. The breach message shows alone while
settling, and the number appears when the countdown actually starts.

## Verification

2 humans + 2 AI, forced warning, sampling every rendered frame:

| | split-screen | shared |
|---|---|---|
| breach → control returns | **3.09s** | **4.33s** |
| breach → countdown *starts* | 0.09s | 1.33s |
| countdown duration | 2.91s | 2.92s |
| `cameraAtTarget` ever true while frozen | yes | yes |

Split is now 3.09s end to end (was ~13s). Its countdown starts almost
immediately because the split camera has nothing to settle — correct, not a
skipped wait. Shared spends 1.33s actually moving the camera, and that time now
shows the breach message with **no digit**, so the countdown visibly starts when
it starts.

`node --check` passes; console and page-error listeners empty in both modes.

## Definition of done

- [x] Split branch sets `cameraAtTarget`
- [x] No digit shown before the countdown starts
- [x] Split total ≈ countdown length; shared shows its travel time honestly
- [x] `docs/TASKS.md`: T67 → `DONE`
