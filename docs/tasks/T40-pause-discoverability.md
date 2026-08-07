# T40 — Make pause discoverable

**Track:** J · **Depends on:** — · **Risk:** very low

Read `docs/AGENT_CONDUCT.md`.

## The complaint

> "We need a pause click/button."

## It already exists — that is the actual bug

T24 added `#pauseMenuBtn` (a ☰ button, fixed top-right), `togglePauseMenu()` and
a `paused` flag, and the CSS shows `display: flex` with no touch-only gate. So it
is on screen on desktop too — **and the owner still did not find it.**

Treat this as a discoverability problem, not a missing feature. Establish first,
in `## Findings`: is the button actually visible during play on a desktop
viewport, or is it hidden behind `.hidden-ui`, drawn under the canvas, or
transparent against the dark background? Screenshot mid-round at 1280×1024 and
look.

## Fix whatever you find, then make it unmissable

- Ensure it is visible and legible mid-round on desktop and mobile — sufficient
  contrast and z-index above the canvas.
- **Add `Escape` and `P` as keyboard shortcuts.** Check both against all four
  `playerConfigs` first. This is what most players will reach for.
- Show a brief hint on the first round of a session ("Esc or ☰ to pause"), fading
  after a few seconds — no persistent clutter.
- Confirm pausing actually freezes `survivalTime`, so mitosis and infection
  timers do not fire on resume, and that rendering continues (a frozen canvas
  behind a menu looks broken).

## Verification

1. Console clean; `## Findings` explains why it was missed.
2. Screenshot mid-round showing the button clearly visible, desktop and mobile.
3. `Escape` and `P` both pause and resume; neither steers any player in a
   4-player round.
4. `survivalTime` does not advance while paused (read it before and after 5 s).
5. Resume continues cleanly with no position jump from accumulated delta.
6. Pausing mid-mitosis and resuming does not desync the event.
