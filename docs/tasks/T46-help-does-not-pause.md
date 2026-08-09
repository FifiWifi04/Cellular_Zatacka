# T46 — Opening Help does not actually pause the round

**Track:** J · **Depends on:** T41 · **Risk:** low · **Est. diff:** ~10 lines

Owner report, 2026-08-09: *"when clicking 'Help' the game is not paused but it
continues it should be paused instead."*

---

## Cause

`toggleHelpPanel(true)` does the right thing — it hides `#ui`, shows the
overlay, and sets `paused = true`. Something else immediately unsets it.

That something is the desktop hover-peek from T24:

```js
uiElement.addEventListener('mouseleave', () => {
    if (isPlaying) { uiElement.classList.add('hidden-ui'); paused = false; }
});
```

The Help button lives **inside** `#ui`, so the cursor is over the panel when it
is clicked. `toggleHelpPanel(true)`'s first act is `classList.add('hidden-ui')`,
which slides the panel out from under that cursor — firing `mouseleave`, whose
handler resumes the round the overlay had just paused. The `paused = true` on
the next line runs first and is then overwritten.

Measured before the fix (1280×800, 2 players, shared camera): `paused` was
already `false` on the very next evaluate after the click, and `survivalTime`
advanced 1.3s over the following 2.5s with the overlay open.

The `document` `pointerdown` resume path had already been given exactly this
guard when T41 landed — the `mouseleave` path was simply missed.

## Fix

One shared predicate, used by all three paths that have to defer to the overlay:

```js
function helpIsOpen() {
    return !document.getElementById('helpOverlay').classList.contains('hidden-help');
}
```

- `mouseleave` on `#ui` → `if (helpIsOpen()) return;` **(the actual fix)**
- the outside-click `pointerdown` resume and the Escape/P branch → switched from
  their inline `classList.contains` checks to `helpIsOpen()`, so the next path
  that needs this rule has one obvious thing to call instead of a fourth copy of
  the string.

## Verification

Desktop (1280×800, real mouse: hover the trigger strip → ☰ → click Help) and
touch (844×390, `has_touch`+`is_mobile`), 2 players, shared camera:

| | desktop | touch |
|---|---|---|
| `paused` after ☰ | true | true |
| `paused` immediately after Help | **true** | **true** |
| `paused` 2.5s later / `survivalTime` delta | true / **0.00** | true / **0.00** |
| after ✕ close, 2.5s later | false / +1.1s | false / +2.5s |
| Escape with Help open | closes Help, resumes | closes Help, resumes |

Console clean in both. Screenshots: `/tmp/verify/t46-{desktop,touch}-help-open.png`.

## Definition of done

- [x] Help pauses and stays paused on desktop and touch
- [x] Closing (✕, outside click, Escape) resumes
- [x] `dist/` rebuilt
- [x] `docs/TASKS.md`: T46 → `DONE`
