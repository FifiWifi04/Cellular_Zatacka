# T19 — Quick Play button

**Track:** E · **Depends on:** T03 · **Risk:** low · **Est. diff:** ~40 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

A prominent "Quick Play" button that skips all configuration and launches a
1-player match against an AI bot instantly.

Roadmap 5.1:

> Re-engineer HTML UI landing menus. Add a prominent "Quick Play" button that
> skips configurations and launches a 1-player match against an AI Bot instantly.

---

## Why it depends on T03

Quick Play's entire value is that the default experience is good. Today's bot
ignores rewards, ignores the bridge, and wobbles — shipping a one-click button
straight into that is worse than no button. T03 fixes the bot; this task exposes
it.

---

## Prerequisites

Read: the `#ui` block in the HTML, `window.updateUI`, `window.startRound`, and the
CSS for `.controls` / `#ui` / `.hidden-ui`. Note that `startRound()` reads its
configuration from the DOM selects:

```
currentMode = parseInt(modeSelect.value);
aiCount     = parseInt(aiSelect.value);
cameraMode  = document.getElementById('cameraSelect').value;
currentSpeed = ...speedSelect...
```

So Quick Play must set those values (or bypass them) **consistently**, or the
round will start with stale settings.

---

## Design

### Behaviour

`Quick Play` = 1 human player, 1 AI bot, shared camera, Normal speed, start
immediately.

Implement it by **setting the selects and then calling the existing start path**,
not by duplicating `startRound()`'s logic:

```
window.quickPlay = function () {
    modeSelect.value   = '1';
    aiSelect.value     = '1';
    document.getElementById('cameraSelect').value = 'shared';
    speedSelect.value  = '1.5';
    updateUI();          // keep the derived state in sync
    startRound();
};
```

This guarantees Quick Play and the manual path can never diverge. Verify by
reading `updateUI()` — check whether it has side effects beyond text (it appears
to clamp `aiCount` against `currentMode`; read it and confirm 1+1 is a legal
combination that it will not rewrite).

> Note the existing clamp: `aiSelect.value = aiCount.toString();` in `updateUI`
> suggests it can rewrite the AI count. Read that logic and make sure a 1-player +
> 1-bot configuration survives it. If it does not, that clamp is the bug to fix,
> and it belongs in this task.

### Presentation

- Place the button **above** the `.controls` row, visually dominant: larger,
  full-width of the panel, high-contrast, distinct from the existing buttons.
- Keep the existing "Start Game" button — it is the configured path. Quick Play
  sits above it with the config controls below, so the hierarchy reads
  "one click, or configure".
- Match the existing aesthetic. Read the current CSS and extend it; do not
  introduce a new design language.
- Keyboard: `Enter` on the landing menu triggers Quick Play. Make sure this does
  not fire while a round is running (`isPlaying`), and does not conflict with the
  dev hotkeys or player controls.

### The menu-visibility interaction

`startRound()` does `uiElement.classList.add('hidden-ui')`, and there is a
hover-to-peek mechanism via `#ui-trigger`. Confirm Quick Play leaves the UI in the
same state the normal start path does — no half-hidden menu.

---

## Files touched

`260703_Cellsnake.html` only: the `#ui` markup, its CSS, `window.quickPlay`, one
`keydown` case. Possibly the `updateUI()` AI-count clamp.

---

## Verification

1. Console clean.
2. **One click starts a playable game**: 1 human + 1 bot, shared camera, Normal
   speed. Verify by reading `players` in the console — exactly 2 entries, one
   with `isBot === true`.
3. **The bot is competent.** It must survive ≥30s and visibly collect at least
   one vesicle (this is the T03 dependency paying off). If it does not, stop —
   T03 is not actually done.
4. **Selects reflect reality** after Quick Play — the menu must not claim a
   different configuration than what is running.
5. **Manual path still works.** Configure 4 players + 0 bots + split + Very Fast
   via the selects and press Start Game. Must behave exactly as before.
6. **Quick Play after a manual round.** Play a 4-player round, return to the
   menu, press Quick Play. Must give 1+1, not leftovers.
7. **`Enter` shortcut** works on the menu and does nothing mid-round.
8. **Layout.** Check at 1280×1024 and at a narrow window. Nothing overflows or
   overlaps.

## Definition of done

- [ ] Quick Play sets the selects and reuses `startRound()` — no duplicated logic
- [ ] `updateUI()`'s AI-count clamp verified against the 1+1 configuration
- [ ] Button is visually dominant and matches the existing style
- [ ] `Enter` shortcut, guarded on `isPlaying`
- [ ] Manual configuration path unchanged
- [ ] `docs/TASKS.md`: T19 → `DONE`
