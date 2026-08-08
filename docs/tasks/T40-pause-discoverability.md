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

## Findings

`#pauseMenuBtn` is a direct child of `<body>` (not nested inside `#game-container`
or any transformed ancestor), styled `position: fixed; top/right: ~12px; width/
height: 44px; z-index: 110;` with a `#2d3436` dark-gray background and a white
`&#9776;` glyph (button text color is `#fff` from the global `button` rule). The
canvas sits at `z-index: 1`, `#ui` at `100`, `#ui-trigger` at `90` — the button is
above all of them and is not touch-gated (`display: flex` unconditionally), so it
**is** on-screen and legible mid-round on desktop at 1280x1024 (confirmed by
screenshot — `/tmp/verify/pause_btn.png`).

So the button is not hidden, transparent, or mis-stacked — it is legitimately a
44px icon-only glyph in a screen corner with no label, no tooltip beyond an
`aria-label` (screen-reader only, invisible during play), and no onboarding cue.
Nothing on screen tells a new player it exists or does anything, and there was no
keyboard shortcut, so a player used to Escape/P for pause from other games had no
way to find it except accidentally hovering/tapping that exact corner. That is
the actual discoverability bug — fixed below with keyboard shortcuts (the "reach
for" affordance) plus a one-time first-round hint (the "look here" affordance),
not a visibility/contrast/z-index fix.

**Second finding, while building and testing the hint element itself:** a fixed-
position hint div stacked above the canvas with `pointer-events: none` rendered
completely invisible in this sandbox's headless/software-rendered Chromium —
`elementFromPoint` at its own center returned the `<canvas>` beneath it, and
pixel-sampling the screenshot showed no trace of the hint's background or text at
all, even with an intentionally loud red background swapped in for the test.
Playwright's own actionability check independently agreed ("element is not
visible"). Isolated A/B testing (own scratch copy, `pointer-events` toggled with
nothing else changed) showed removing `pointer-events: none` alone was sufficient
— the element then painted correctly and passed every check. `pauseMenuBtn` (a
plain `<button>`, no `pointer-events` at all) was never affected, which is why the
existing pause button rendered fine throughout. The shipped `.pause-hint` CSS
does not set `pointer-events`; it doesn't need to, since the hint sits below
`pauseMenuBtn` with no overlap and fades on its own after ~3.6s, so leaving it
default (auto) costs nothing. Root cause not fully diagnosed (likely a
compositing-layer ordering quirk specific to this environment's software WebGL
path), so noted in `docs/BACKLOG.md` as a trap for any future task that stacks a
`pointer-events: none` overlay above the canvas and verifies it via screenshot in
this harness.

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
