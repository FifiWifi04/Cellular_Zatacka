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

- [x] Touch button, shown only when owned, drives players[0]
- [x] Cooldown state visible on the button
- [x] Shop description no longer says "Press X" on touch
- [x] Does not steal steering input
- [x] Desktop unchanged
- [x] `docs/TASKS.md`: T59 → `DONE`

---

## Findings

**Button placement.** `#shedTailBtn` (`.shed-tail-btn`, 56x56 circle) sits in
the bottom-left corner — the mirror image of T23's `#touchToggleBtn`
(bottom-right) and clear of `#pauseMenuBtn` (top-right). All three corners
stay non-overlapping at both 390x844 and 844x390 (measured
`getBoundingClientRect()`: shedTail `x:16-72,y:318-374`, toggle
`x:772-828,y:318-374`, pause `x:788-832,y:12-56` at 844x390 — no intersection).
Screenshotted both sizes, `/tmp/verify/t59_390x844.png` and
`/tmp/verify/t59_844x390.png`.

**Visibility.** Hidden by default (CSS `display:none`); shown/hidden every
rendered frame by a new draw-only `updateShedTailButtonHUD()` (§4.4a, mirrors
`updateNucleusFeedHUD()`'s exact show/hide idiom) gated on
`isTouchDevice && players[0].alive && players[0].upgrades.shedTail` — the
same ownership flag T55 already resolves once at round start, so local
multiplayer/online play (where `resolvePlayerUpgrades()` always returns an
empty `owned`) hides it automatically with no extra gating needed. Verified:
`display:none` before granting the upgrade, `display:flex` after (owned via
direct `saveHighScores()` injection, same schema the real shop purchase
writes).

**Activation and trace cut.** `touchShedTail()` reuses the exact same
condition as the existing 'x' keydown handler and the bot's own use of the
ability in `updatePlayers()` (`p.alive && !p.isBot && p.upgrades.shedTail &&
survivalTime - p.effects.lastShedTail > SHED_TAIL_COOLDOWN`), and calls the
same `deleteOldestTrace(p, SHED_TAIL_FRACTION)`. Measured atomically (before/
after read in the same JS tick, so the player's own continuous forward growth
can't mask the cut): 25 → 18 points (a live tap), and separately 143 → 101
after a forced cooldown expiry — both ≈30% (`SHED_TAIL_FRACTION`), matching
the keyboard path exactly.

**Cooldown.** An immediate second call in the same tick is a no-op (18 → 18).
The button reflects this: `disabled=true` and its label switches from the
scissors glyph to a live `Math.ceil()` countdown (`"30"` immediately after
use, `"29"`s after a short wait) the very next rendered frame. Forcing
`lastShedTail` back past `SHED_TAIL_COOLDOWN` returns the button to
`disabled=false` and the scissors glyph, and a real tap through it cuts the
trace again — cooldown recovery confirmed both in state and via the DOM.

**Steering never stolen.** `document.elementFromPoint()` swept across both
viewports returns `CANVAS` everywhere except the two 56x56 button footprints
themselves (top-left/top-right/center/just-outside-each-button all hit the
canvas; only the exact button rectangles hit `shedTailBtn`/`touchToggleBtn`).
A synthetic held `pointerdown`(pointerType:`touch`) dispatched at the canvas
elsewhere sets `keys.ArrowLeft=true` for the duration of the hold and clears
it on `pointerup` — steering is unaffected, unlike the T45 `#ui-trigger` strip
that used to swallow the whole top 30px.

**Desktop unchanged.** `isTouchDevice=false` keeps `shedTailBtn` at
`display:none` throughout (before and after granting the upgrade); the 'x'
keydown handler still cuts the trace on its own (203 → 156 points, a live,
non-atomic sample — consistent with ≈30% given trace kept growing during the
sampling wait).

**Shop text.** `UPGRADES.shedTail.desc` is now a function of `isTouchDevice`
(`renderShopPanel()` calls it if it's a function, string otherwise — the only
upgrade that needs to vary). Rendered text: desktop —
*"Cut away the oldest third of your own trace with 'X'. Long cooldown."*;
touch — *"...with the scissors button. Long cooldown."* Neither device shows
"Press X" anymore.

**Verified:** console clean over both `http://` (harness) and `file://`
(`dist/`, offline); `node --check` on the extracted script; a real 20.2s
round (1 human + 3 bots, no touch) played normally, no console errors;
`tools/build_standalone.py --check` passes. `sw.js` `CACHE_NAME` bumped
v39→v40; `dist/` rebuilt. No hazard was added or changed (`checkCollision`,
`checkArcCollision`, `raycast`, `rebuildSpatialGrid` do not appear in the
diff — confirmed by grep), so AGENT_CONDUCT §4.1/§7.6 don't apply here, same
reasoning T54/T55 recorded for their own no-hazard-touched diffs.
