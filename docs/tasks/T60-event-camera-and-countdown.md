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

- [ ] Every camera lerp time-based; 60fps feel preserved and the mapping stated
- [ ] Resume gated on camera settle, not on 5.0s
- [ ] One countdown, reused by all three freezing events, frame-rate independent
- [ ] T57's separate grace folded in
- [ ] Zoom change after control returns ≈0, measured at two frame rates
- [ ] Reveal framing fits the two cells at any aspect ratio
- [ ] `docs/TASKS.md`: T60 → `DONE`

---

## Findings

*(Rate mapping; the before/after zoom-tail table at both frame rates; countdown
timing at both; the 5-event no-death run.)*
