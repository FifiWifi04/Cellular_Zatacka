# T45 — The start menu never leaves the screen on mobile

**Track:** J · **Depends on:** — · **Risk:** low (CSS only) · **Est. diff:** ~20 lines

Owner report, 2026-08-08, on an installed Android PWA in landscape split-screen:
*"it is working, the starting menu does not disappear completely during the game
tho."* The screenshot showed the bottom band of the panel — the mode/camera
buttons and the P1/P2 labels — parked across the top of the arena for the whole
round.

---

## Cause

`startRound()` adds `hidden-ui`, and that class only ever slid the panel up by
90% of **its own height**:

```css
#ui.hidden-ui { transform: translate(-50%, -90%); }  /* "Leaves a tiny sliver visible" */
```

The sliver is deliberate on desktop: it is the visual hint that the panel is up
there and that moving the mouse into `#ui-trigger` (a 30px invisible strip at
`top: 0`) pulls it back down.

It stops being tiny on a phone. T24 gave `#ui` `min-width: min(400px, 94vw)`,
`max-height: 90dvh` and `padding-top: max(15px, env(safe-area-inset-top))`, so
the panel is much taller there — measured 351px on an 844×390 landscape
viewport. 10% of that is a 35px band, plus the 20px downward bleed of
`box-shadow: 0 4px 20px`, over an arena only 390px tall.

And the sliver buys nothing on touch, because T24 already gated the
`mouseenter`/`mouseleave` listeners to `!isTouchDevice` and added
`#pauseMenuBtn` (☰, top-right) as the touch affordance. So on touch the sliver
is a hint to a gesture that is not bound, and `#ui-trigger` is 30px of arena
that silently swallows steering `pointerdown`s before they reach the canvas.

## Fix

Both rules keyed off `body.touch-ui`, the class T24 already sets from
`isTouchDevice` — one source of truth for "this is a touch device", rather than
a second, subtly different media query.

- `body.touch-ui #ui.hidden-ui` → `translate(-50%, calc(-100% - 24px))`.
  `-100%` puts the panel's bottom edge exactly on `y = 0`; the extra 24px clears
  the box-shadow.
- `body.touch-ui #ui-trigger` → `display: none`, returning the top 30px of the
  screen to steering.

Desktop is untouched: same `-90%`, same live trigger strip.

## Verification

Landscape 844×390 with `has_touch`/`is_mobile`, versus 1280×800 desktop, both
in a 2-player split-screen round.

| | touch | desktop |
|---|---|---|
| `pointer: coarse` / `isTouchDevice` / `.touch-ui` | true | false |
| menu px on screen while playing | **0** (`top −375`, `bottom −24`) | 48 (unchanged) |
| `#ui-trigger` computed display | `none` | `block` |
| `elementFromPoint(centre, y=8)` | `CANVAS` | `#scoreboard` (the sliver) |
| ☰ reopens the menu | yes, back to `top: 0` | n/a |

Console clean apart from the two `favicon.ico` 404s the harness documents as
TRAP 2. Screenshots: `/tmp/verify/t45-touch.png` (clear arena),
`t45-touch-reopened.png` (☰ pulls the panel back).

**Measurement note for future sessions:** a fixed `wait_for_timeout` after
`startRound()` reads the rect *before* the 0.4s slide has run about half the
time — under software WebGL the compositor is starved for seconds. Poll until
`getComputedStyle(el).transform` stops changing instead. Two consecutive runs
were byte-identical once polled.

## Definition of done

- [x] Menu fully off-screen during play on touch
- [x] `#pauseMenuBtn` still brings it back
- [x] Desktop hover-peek sliver and trigger strip unchanged
- [x] `dist/` rebuilt
- [x] `docs/TASKS.md`: T45 → `DONE`
