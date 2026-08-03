# T24 — Mobile: touch-friendly menu and HUD

**Track:** H (Phase 6) · **Depends on:** T23 · **Risk:** low · **Est. diff:** ~110 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Make the menu and in-game UI usable with a thumb.

## Why

The current UI assumes a mouse in two places that simply do not exist on touch:

```
uiTrigger.addEventListener('mouseenter', () => uiElement.classList.remove('hidden-ui'));
uiElement.addEventListener('mouseleave', () => { ... });
```

`startRound()` hides the menu with `.hidden-ui`, and the only way to get it back
is hovering `#ui-trigger`. **On a phone the menu becomes permanently
unreachable once a round starts.** There is also no visible pause or exit.

Secondary issues: native `<select>` dropdowns are workable but cramped, and the
buttons are sized for a cursor.

---

## Design

### 1. Replace hover-peek with an explicit control

Keep the hover behaviour for mouse users (it is nice), but add a real button that
works for everyone:

- A small persistent **menu/pause button** in a screen corner, ≥44×44 CSS px,
  clear of the safe-area insets from T23.
- Tapping it opens the menu and **pauses the round** if one is running.
- Tapping outside the menu, or a close button, resumes.

Gate the hover listeners on `!isTouchDevice` (the flag T23 added) so a phone
never enters the hover path at all.

### 2. Pause — check whether it exists

Read `gameLoop` and `startRound` first and record the answer in `## Findings`:
is there any pause today? The game has `app.ticker.stop()` in the solo game-over
path, and `isPlaying`, but no player-initiated pause.

If pausing is new, keep it minimal and honest: set a `paused` flag that makes
`gameLoop` return early **after** the `isPlaying` check but **before**
`stepSimulation`. Do not stop the ticker — that also freezes rendering, and a
frozen canvas behind a menu looks broken. Confirm `survivalTime` does not
advance while paused, or the mitosis and infection timers will fire on resume.

In multiplayer (Phase 7) a local pause must not pause other players — note that
in the code comment so nobody assumes it will.

### 3. Touch sizing

- Every interactive element ≥44×44 CSS px with ≥8px spacing.
- Increase `<select>` and `<button>` padding and font-size when
  `isTouchDevice` — a CSS class on `<body>` is the smallest way to do this.
- The menu panel should be scrollable if it exceeds the viewport in landscape on
  a short screen (`max-height: 90dvh; overflow-y: auto`). Use `dvh`, not `vh` —
  mobile browser chrome makes `vh` wrong.

### 4. Quick Play is the mobile default

T19 adds a Quick Play button (1 human + 1 bot). On a touch device that is the
*only* sensible mode until Phase 7, so:

- When `isTouchDevice`, make Quick Play the visually dominant action and
  de-emphasise the player-count selector.
- If the player picks 2–4 players on a touch device, show a short inline note
  that multiple players need a keyboard (or networked play, once it exists).
  Do not silently allow a broken configuration.

If T19 has not landed yet, do not build Quick Play here — just leave the menu
touch-usable and note the dependency.

### 5. HUD legibility

The scoreboard and warning text are sized for a desktop viewport. Scale them with
`clamp()` so they stay readable on a 390px-wide screen without dominating a
desktop one.

---

## Files touched

`260703_Cellsnake.html` only: `#ui` markup, CSS, the hover listeners, a pause
flag in `gameLoop`, the menu/pause button handler.

---

## Verification

1. Console clean.
2. **Menu reachable mid-round on touch.** Start a round in a 390×844 emulated
   viewport, tap the menu button, menu opens, game pauses.
3. **Pause is real.** `survivalTime` does not advance while paused; confirm by
   reading it before and after a 5-second pause. Rendering continues.
4. **Resume works** and the game continues from where it stopped — no jump in
   player position from an accumulated delta.
5. **Hover still works on desktop** and is not registered on touch devices.
6. **Tap targets.** Every button ≥44×44 CSS px — measure with
   `getBoundingClientRect()` in the harness, do not eyeball it.
7. **Menu fits** in landscape on a short screen (e.g. 844×390) and scrolls if not.
8. **Desktop unchanged.** Full keyboard round, menu behaviour identical to before.

## Definition of done

- [ ] `## Findings` records whether pause existed before this task
- [ ] Menu reachable mid-round without hover
- [ ] Pause freezes `survivalTime` but not rendering
- [ ] All tap targets ≥44px, verified by measurement
- [ ] `dvh` used for viewport-relative heights
- [ ] Desktop mouse/keyboard experience unchanged
- [ ] `docs/TASKS.md`: T24 → `DONE`; T25 → `READY`

---

## Findings

*(Does a pause mechanism exist today? Where did you hook it, and what else reads
`survivalTime` that pausing affects?)*
