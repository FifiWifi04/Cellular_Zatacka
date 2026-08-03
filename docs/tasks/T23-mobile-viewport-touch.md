# T23 — Mobile: viewport, touch input, orientation

**Track:** H (Phase 6) · **Depends on:** — · **Risk:** low · **Est. diff:** ~120 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Make the game **playable at all** on a phone: correct viewport, touch steering,
sane orientation handling. This is the enabling task for all of Phase 6.

## Why

Three verified blockers:

- **No viewport meta tag.** Grep confirms the only `viewport` occurrence in the
  file is a code comment. Without `<meta name="viewport">`, mobile browsers lay
  out at a virtual ~980px width and scale the result down — everything is tiny
  and touch coordinates are wrong.
- **Zero touch handling.** `grep -c "touchstart|pointerdown|touch-action"`
  returns **0**. Input is entirely `keys[e.key]`, so a phone cannot steer at all.
- **Browser gestures fight the game.** Without `touch-action` and
  `overscroll-behavior`, dragging pulls-to-refresh and double-tap zooms.

## Scope note — one player per device

A phone gives you one pair of thumbs, so mobile means **solo vs. bots** (Quick
Play, T19) until Phase 7 lands networked multiplayer. Do not attempt split-thumb
local 2-player; it is cramped and not worth the complexity. Say so in the UI if
the player picks a multi-player mode on a touch device.

---

## Design

### 1. Viewport and gesture suppression

In `<head>`:

```
<meta name="viewport" content="width=device-width, initial-scale=1,
      maximum-scale=1, user-scalable=no, viewport-fit=cover">
```

In CSS on `html, body, #game-container`:

```
touch-action: none;              /* no pan/zoom gestures stolen from us */
overscroll-behavior: none;       /* no pull-to-refresh */
-webkit-user-select: none; user-select: none;
-webkit-tap-highlight-color: transparent;
```

`viewport-fit=cover` plus `env(safe-area-inset-*)` padding on the UI keeps
controls clear of notches and home indicators.

### 2. Touch steering

The genre standard, and it fits the existing input model: **left half of the
screen turns left, right half turns right.** Hold to keep turning.

Implement it by feeding the **existing `keys` object**, not by adding a parallel
input path:

```
// a touch in the left half sets keys[<player 1 left control>] = true
```

That way `gameLoop`'s existing `if (keys[p.controls.left])` works unchanged, bots
are unaffected, and there is exactly one input model to reason about.

Requirements:
- Listen on `pointerdown` / `pointermove` / `pointerup` / `pointercancel`
  (Pointer Events cover mouse, touch and pen in one API — do not use
  `touchstart` directly).
- **Track pointer IDs.** A finger sliding from the left half to the right half
  must switch direction; lifting one of two fingers must not cancel the other.
  Keep a `Map` of active pointer id → which half, and recompute the key state
  from the set of active pointers each event.
- `pointercancel` must release everything — it fires when the browser takes over
  the gesture, and a missed release means the player spins forever.
- Release all touch-driven keys on `visibilitychange` when the page is hidden.

### 3. The `targetMode` toggle

The third control has no natural touch gesture. Use a **small on-screen button**
in a bottom corner, styled to match the existing UI, showing the current mode by
colour (green = `self`, red = `attack`) to match the in-game aura. Make it at
least 44×44 CSS px — smaller is unreliable to hit.

Do not use double-tap: it conflicts with steering and adds latency to every tap.

### 4. Orientation

The arena is a wide ellipse (2800×2400 world units) and the camera auto-zooms, so
landscape is the better fit but portrait must not break.

- Do not hard-lock orientation (it needs fullscreen on most browsers and annoys
  users). Instead, handle both: the existing `resize` handler already recalculates
  `SCREEN_WIDTH`/`SCREEN_HEIGHT` — confirm it also fires on `orientationchange`
  and that `updateCamera()`'s zoom maths still frames the arena sensibly in a tall
  aspect ratio.
- If portrait is genuinely unplayable after testing, show a "rotate your device"
  overlay rather than locking.

### 5. Detection

Add one flag, used by this task and later by T24/T26:

```
const isTouchDevice = window.matchMedia('(pointer: coarse)').matches;
```

Prefer this over user-agent sniffing. Note that a touchscreen laptop reports
coarse pointer too — so use it to *enable* touch controls, never to *disable*
keyboard ones. Both must work simultaneously.

---

## Files touched

`260703_Cellsnake.html` only: `<head>` meta, CSS, new pointer handlers near the
existing `keydown`/`keyup` listeners, a toggle button in the UI markup.

---

## Verification

Real hardware if you have it; otherwise Chromium device emulation via the
harness (`page.emulate_media`, touch-enabled context, and a mobile viewport).

1. Console clean.
2. **Renders at device scale.** In a 390×844 viewport the UI is legible and the
   canvas fills the screen — not a scaled-down 980px layout.
3. **Steering works.** Holding the left half turns left; the right half turns
   right; releasing stops the turn.
4. **Pointer-ID handling.** Slide one finger from left half to right half — the
   turn direction must follow. With two fingers down, lift one — the other must
   still steer.
5. **`pointercancel` releases.** Simulate a cancel and confirm the player stops
   turning rather than spinning indefinitely.
6. **Backgrounding releases.** Switch tabs mid-turn, come back — the player is
   not still turning.
7. **No browser gestures.** Dragging does not scroll or pull-to-refresh;
   double-tap does not zoom.
8. **Keyboard still works** on desktop, completely unchanged. Play a 4-player
   keyboard round to confirm nothing regressed.
9. **Both orientations** render without clipping; the arena stays framed.
10. **Toggle button** switches `targetMode` and reflects it by colour.

## Definition of done

- [ ] Viewport meta + gesture suppression CSS in place
- [ ] Touch steering feeds the existing `keys` object — no parallel input path
- [ ] Pointer IDs tracked; cancel and backgrounding both release cleanly
- [ ] `targetMode` button, ≥44px, colour-coded
- [ ] Keyboard input demonstrably unchanged
- [ ] Both orientations verified
- [ ] `docs/TASKS.md`: T23 → `DONE`; T24 → `READY`
