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

- [x] `## Findings` records whether pause existed before this task
- [x] Menu reachable mid-round without hover
- [x] Pause freezes `survivalTime` but not rendering
- [x] All tap targets ≥44px, verified by measurement
- [x] `dvh` used for viewport-relative heights
- [x] Desktop mouse/keyboard experience unchanged
- [x] `docs/TASKS.md`: T24 → `DONE`; T25 → `READY`

---

## Verification results — 2026-08-07

All via `tools/verify_harness.py` (`node --check` on the extracted script also
passed, and `python3 tools/build_standalone.py --check` is clean):

1. **Console clean** — confirmed across every check below (`assert_console_clean()`),
   over both `http://` and `file://`.
2. **Menu reachable mid-round on touch** — 390×844 context with `has_touch=True,
   is_mobile=True` (so `isTouchDevice` reads `true` exactly as it would on a real
   phone): `pauseMenuBtn` click reveals `#ui` (`hidden-ui` removed) and sets
   `paused = true` while `isPlaying`.
3. **Pause is real** — `survivalTime` measured immediately after the pause-button
   click (not before — `page.click()` itself costs real wall time during which the
   still-unpaused game keeps running) stayed byte-identical across a 2s wait
   (`4.3997` → `4.3997`); `app.ticker.started` stayed `true` throughout, and an
   instrumented `gameLoop` wrapper confirmed it is being called every tick and
   returning early on the `if (paused) return;` guard.
4. **Resume works, no jump** — closing via `#uiCloseBtn` sets `paused = false`;
   over the next 1.5s wall-clock wait `survivalTime` advanced ≈1.4s (bounded by
   the wait itself, not by the ~1s the round had been paused) — expected, since
   the ticker is never stopped so `deltaMS` on resume is only the last
   inter-frame gap, not the whole paused duration.
5. **Hover** — real mouse (`page.mouse.move`), non-touch context: hovering the
   trigger strip reveals the menu without pausing (`paused` stays `false`);
   crossing the revealed panel and leaving re-hides it. (Confirmed via
   `git stash`/`git stash pop` that a synthetic hover landing on the exact
   center column of the trigger strip is a pre-existing quirk — the still-hidden
   `#ui`'s own translated sliver outranks `#ui-trigger` there on z-index — not
   something this task introduced or fixed; logged in `docs/BACKLOG.md`.) On a
   touch-emulated context, a synthetic `mouseenter` dispatched at `#ui-trigger`
   produced no reveal (`hidden-ui` stayed `true`), confirming the `!isTouchDevice`
   gate.
6. **Tap targets** — `getBoundingClientRect()`: `#pauseMenuBtn` 44×44,
   `#uiCloseBtn` 44×44, `#quickPlayBtn` ≥44 tall (52) and full-width.
7. **Menu fits / scrolls** — 844×390 (landscape-short): computed `max-height`
   351px (90dvh of 390), `overflow-y: auto`; `scrollHeight` 642 > `clientHeight`
   349, so the excess scrolls rather than clipping.
8. **Desktop unchanged** — 1024×768, `isTouchDevice=false`,
   `document.body` never gets `touch-ui`; hover peek/hide behaves as above;
   30s solo+bot round (640×480 default) played clean with the bot moving,
   surviving, and traces/vesicles updating normally (screenshot inspected).

**Also fixed (redirected into this task's scope by the T19/T23 backlog notes,
not a drive-by):** `#ui { min-width: 400px; }` clipped part of the menu
off-screen with no way to scroll to it on any viewport narrower than ~410px.
Changed to `min-width: min(400px, 94vw); max-width: 94vw;` — unchanged on
desktop (still resolves to 400px at any normal desktop width), but a 390px or
360px phone now fits with `.controls`' existing `flex-wrap` reflowing the
buttons instead of clipping. Re-verified: `#ui`'s `scrollWidth` no longer
exceeds the viewport at either width (was 460px on a 390px viewport before).

---

## Findings

No player-initiated pause existed before this task. `isPlaying` + `app.ticker.stop()`
were only used for the solo game-over freeze (all bots/players dead); there was no
way to voluntarily pause a live round.

T22 (sim/render split) has not landed, so `gameLoop` is still one fused ~600-line
function with no separate `stepSimulation` to gate before. The earliest point that
is guaranteed to run before any state mutation is right after the existing
`if (!isPlaying) return;` line, so the new `if (paused) return;` was placed there.
The ticker itself is never stopped, so PIXI's own registered render pass keeps
redrawing (unchanged) every frame instead of a `app.ticker.stop()`-style freeze,
and — because the ticker never stops ticking — `app.ticker.deltaMS` on the first
frame after resume is just the last inter-frame gap, not the whole paused
duration, so there is no big-delta jump on resume.

Everything downstream of that early return is skipped while paused, so pausing
also freezes: the mitosis timers (`nextTriggerTime`, `eventStartTime`-relative
progress), the infection/virus timers (`nextWarningTime`, `triggerTime`), the
Gen2+ necrosis timer, the Gen2+ calcification radius shrink, the Gen3+ malignant
mass growth timer, `globalRotation`, and the HUD scoreboard text update — none of
those are driven independently of `gameLoop`, so nothing needed a separate guard.
`startRound()` now also resets `paused = false`, since restarting a round from a
paused menu (via the Start Game button) would otherwise leave the new round
permanently frozen.
