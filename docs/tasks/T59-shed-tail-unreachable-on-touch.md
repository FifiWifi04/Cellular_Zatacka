# T59 — "Shed the Tail" can be bought on mobile but never used

**Track:** J · **Depends on:** T55 · **Risk:** low · **Est. diff:** ~35 lines

Owner report, 2026-08-11: *"the X button for deleting part of the tail after
buying the upgrade does not seem to be available through mobile app."*

Correct — it does not exist there.

---

## Cause

T55 bound the ability to a keyboard key only:

```js
if (isPlaying && !paused && (e.key === 'x' || e.key === 'X')) { … }
```

and describes itself in the shop as *"Press X to cut away the oldest third of
your own trace."* A phone has no X. So the upgrade is purchasable for 1000
points on a device that can never fire it, and its own description tells the
player to do something impossible.

This is the same gap T23 closed for the target-mode toggle, which is why
`#touchToggleBtn` exists. The pattern to copy is already in the file.

## Fix

1. **A second on-screen button for touch**, modelled on `#touchToggleBtn`
   (created in the HTML, `style.display = 'flex'` only when `isTouchDevice`,
   positioned clear of the steering halves and of `#pauseMenuBtn`). It drives
   players[0], the same reasoning T23 recorded for the toggle button.
2. **Only show it when the upgrade is owned.** An always-present button for an
   ability the player has not bought is noise, and it would tell a new player
   about a mechanic they cannot use.
3. **Show the cooldown on the button itself.** `SHED_TAIL_COOLDOWN` is 30s —
   without feedback a tap during cooldown looks like a broken button. Disabled
   state plus a countdown or a radial sweep; reuse whatever the HUD already
   does for timers rather than inventing a third idiom.
4. **Fix the description.** The shop line must not say "Press X" on a touch
   device. Derive it the way T41's help panel already derives its text from live
   state, or word it neutrally ("Cut away the oldest third of your own trace").

## Verification

1. Console clean.
2. On touch, with the upgrade **not** owned: no button.
3. On touch, with it owned: button visible, tapping it cuts the oldest third —
   report trace point count before and after.
4. Cooldown honoured and visible: a second tap inside 30s does nothing and the
   button shows why. Report both attempts.
5. The button never swallows a steering `pointerdown` — verify steering still
   works over the whole arena, including under and beside the button (this is
   the mistake T45 found in `#ui-trigger`).
6. Desktop unchanged: X still works, no new button on a mouse device.
7. Shop text correct on both device types; screenshot each.
8. Renders correctly at 390×844 and 844×390 alongside `#pauseMenuBtn` and
   `#touchToggleBtn` — three buttons must not overlap.
9. Regression sweep §7.6.

## Definition of done

- [ ] Touch button, shown only when owned, drives players[0]
- [ ] Cooldown state visible on the button
- [ ] Shop description no longer says "Press X" on touch
- [ ] Does not steal steering input
- [ ] Desktop unchanged
- [ ] `docs/TASKS.md`: T59 → `DONE`

---

## Findings

*(Button placement and why; trace counts before/after; the cooldown evidence.)*
