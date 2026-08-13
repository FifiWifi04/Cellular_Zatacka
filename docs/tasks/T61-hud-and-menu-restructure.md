# T61 — The menu has become a wall, and the HUD collides with itself

**Track:** J · **Depends on:** T53, T54, T55 · **Risk:** low-medium (layout only) · **Est. diff:** ~150 lines

Owner request, 2026-08-11: *"Inspect … the GUI. What could be improved to make it
more appealing, immersive and clear to navigate?"*

Every one of these was found in a captured screenshot, not by reading code.
Screenshots referenced are under `/tmp/verify/audit/`.

---

## 1. The nucleus bar is drawn on top of the scoreboard

`12-gen4-transformed.png`: the word **NUCLEUS** and its red progress bar sit
directly over `P1: 0 | P2: 0 | P3: 0 | P4: 0`. Both are unreadable. Two HUD
elements were each given the top-centre slot without either knowing about the
other.

**Fix:** one HUD stack with a defined order, not independently-positioned
elements. Everything that lives at the top-centre — scoreboard, nucleus meter,
ATP pause bar, generation label — goes in a single flex column so adding the next
one cannot overlap the last.

## 2. The control legend is printed twice

`15-end-card.png`: *"3rd key toggles boost target: Green = Self … Red = Attack …"*
appears **twice** in the same panel, roughly 60px apart, once above the
`P1: L/R/Down | P2: A/D/S` summary and once below it. And both are redundant with
the per-player cards directly above, which already show a "toggle mode" key each.

**Fix:** one statement of the rule, once, attached to the control cards.

## 3. The post-round panel is a wall of unrelated things

`15-end-card.png` shows, in one scrolling column: Quick Play, five
selects/buttons, a four-player control grid (P3 and P4 greyed out in a 1-v-1),
the duplicated legend, a control summary, the score line, and only then the
stats card — which is **cut off mid-row** at the panel's bottom edge.

The thing the player wants after dying is the result. It is last, below the
setup UI, behind a scroll they are not told about.

**Fix:** separate the two states rather than concatenating them.

- **Round over** → the result first: score, what killed you, the stats, and a
  prominent **Play Again**. Setup collapses to a link/disclosure.
- **Pre-round** → setup, as now, without the results block.

The panel already has a `.hidden-ui` state and a close button; this is a matter
of which children are visible in which state, not new machinery.

## 4. The phone menu is cut off with no scroll affordance

`06-menu-phone.png` (844×390 landscape): "Quality: Auto" and "Start Game" are
sliced in half by the panel edge, and **Controls / Help / Scores / Shop / Online
are entirely below the fold**. T24 gave the panel `max-height: 90dvh` and
`overflow-y: auto`, so it does scroll — but nothing on screen says so, and a
landscape phone is exactly where it matters.

**Fix:** make the overflow visible — a fade or chevron at the cut, or reflow to
two columns in landscape where there is horizontal room to spare. Verify the
primary action stays above the fold at 390px tall.

## 5. Four panels, one shape, no way to tell them apart

Help, Scores, Shop and Online all reuse T41's overlay (correctly — that was the
instruction). But they are now four identical dark rounded rectangles
distinguished only by a heading. Give each a consistent identifying element —
an icon and an accent colour in the header — so a player who opens the wrong one
knows immediately.

## 6. Smaller things worth doing in the same pass

- **P3/P4 control cards show in a 1-v-1.** Greyed-out controls for players who do
  not exist is clutter on the busiest panel in the game. Show only the cards for
  configured players.
- **Two close affordances.** The panel has an `×` at top-left *and* `#pauseMenuBtn`
  (☰) at top-right doing effectively the same job (`01-menu-desktop.png`). Pick one.
- **"Survival Time: 0.0s"** is displayed on the pre-round menu, before a round
  exists. Hide it until there is a time to show.

## Verification

1. Console clean.
2. **No HUD overlap** at Gen 4 with the nucleus meter, the ATP bar and the
   scoreboard all live: screenshot at 390×844, 844×390, 1100×850. This is item 1
   and it is the most visible defect.
3. The boost-target rule appears **exactly once** — grep the rendered DOM.
4. Round-over state shows the result without scrolling at all three sizes;
   Play Again reachable without scrolling. Screenshot each.
5. Phone menu: primary action above the fold at 844×390, and the overflow is
   visibly indicated. Screenshot.
6. Each panel identifiable at a glance; screenshot all four side by side.
7. P3/P4 cards absent in a 1-v-1, present in a 4-player game.
8. Pause/resume behaviour unchanged — T46's rule still holds (opening any panel
   pauses; closing resumes) for all four panels.
9. Nothing in this task touches gameplay: confirm by `git diff` that no
   collision, hazard or timing constant moved.
10. Regression sweep §7.6.

## Definition of done

- [x] Single ordered HUD stack; no overlap at any size
- [x] Legend stated once
- [x] Round-over and pre-round are distinct states; result is first after a round
- [x] Phone overflow indicated; primary action above the fold
- [x] Panels visually distinguishable
- [x] P3/P4 cards conditional; duplicate close affordance resolved; stray timer hidden
- [x] `docs/TASKS.md`: T61 → `DONE`

---

## Findings

**Item 1 (HUD stack).** `#scoreboard` (previously inside `#ui`, only visible
during play via a "peek sliver" left when `#ui.hidden-ui` slid up 90%) and
`#nucleusFeedBar` (previously its own independently fixed-position element)
now both live inside a single new `#liveHud` flex column, always visible and
independent of `#ui`'s own show/hide state. Verified with `activeCell.generation
= 4; nucleusFeed.value = 400` forced live, `#ui` opened on top of it (pause
menu): no overlap at 390x844, 844x390 or 1100x850
(`t61_gen4_hud_paused_*.png`). Fixing this exposed two knock-on bugs, both
fixed in the same diff:
- `#ui`'s own resting `top` had to move down to clear `#liveHud`'s reserved
  space, but `#ui.hidden-ui`'s hide transform (`translate(-50%, calc(-100% -
  24px))`) is relative to `#ui`'s own box, not the viewport -- it doesn't
  automatically compensate for a changed `top`. The first version left a
  48px sliver of `#ui`'s own bottom content visible at the top of the screen
  whenever `#ui` was supposedly hidden (caught by directly reading
  `getBoundingClientRect()` while `helpOverlay` was open, not by eye). Fixed
  with a shared `--ui-top-offset` custom property that both `#ui`'s `top`
  and the hide transform read, including inside the new landscape media
  query (item 4) so the two can't drift out of sync again the way they just
  did once.
- `#liveHud` and the four modal overlays (Help/Scores/Shop/Online) share the
  same `z-index: 150`; since `#liveHud` is deliberately independent of
  `#ui`'s hide state, it kept rendering (dimmed, through the overlay's
  `rgba(0,0,0,0.6)` scrim) above the modal panel instead of being covered by
  it. Fixed with `updateLiveHudVisibility()`, a `MutationObserver` on each
  overlay's own `hidden-help` class toggle (not a change to the four
  `toggleXPanel()` functions themselves) that adds `.hidden-hud` to
  `#liveHud` while any one of them is open. Screenshots of all four panels
  confirm no bleed-through (`t61_panel_help.png`,
  `t61_panel_scores.png`, `t61_panel_shop.png`, `t61_panel_online.png`).

**Item 2 (legend printed twice).** `updateUI()`'s multiplayer branch no
longer appends `TARGET_MODE_LEGEND` to `#controlsText`; `#splashHint`
(attached to the control cards, `renderControlSplash()`) is now the only
place it renders. Verified by walking every leaf element under `#ui` and
counting matches of the full legend string: **1 occurrence** (was 2, ~60px
apart, per the task's own screenshot).

**Item 3 (round-over is a wall of setup).** New `#roundResult` (stats card +
a prominent `▶ Play Again` button, reusing `.quick-play-btn` styling) is the
first child of `#ui`; the setup controls (Quick Play, mode/AI/camera/speed/
quality selects, Start Game, Fullscreen, Controls/Help/Scores/Shop/Online)
moved into a native `<details id="setupDetails">`, open pre-round and
collapsed the moment `renderStatsCard()` runs (`startRound()` re-opens it for
the next round). Verified by forcing a real membrane death at all 3 speeds
(the §7.6 sweep below) and reading DOM state right after:
`roundResultHidden: false`, `setupOpen: false`, `needsScroll: false`,
`playAgainWithinViewport: true` at 390x844, 844x390 and 1100x850 -- the
result renders complete and reachable with **zero scrolling** at every
tested size (`t61_roundover_390x844.png` etc). Clicking `#playAgainBtn`
correctly calls `startRound()`: `isPlaying` flips back to `true`,
`survivalTime` resets, `#roundResult` re-hides, `#setupDetails` re-opens,
`#ui` re-hides (auto-hide-on-start, unchanged).

**Item 4 (phone landscape overflow).** Two independent fixes:
- `#ui.has-more-below::after` -- a sticky bottom gradient fade, toggled by
  `updateUiScrollCue()` (a scroll listener + a `MutationObserver`, not a
  `ResizeObserver`: `#ui` is already clamped at `max-height: 90dvh`, so its
  own box stops growing once content overflows it, and a `ResizeObserver` on
  `#ui` itself would miss further content changes past that point).
  Confirmed `hasMoreBelow: true` exactly when `scrollHeight > clientHeight`.
- A `@media (max-height: 420px) and (orientation: landscape)` block reclaims
  vertical space (smaller `--ui-top-offset`, tighter padding/gaps, and a
  touch-ui-specific size reduction scoped to `#ui` only) so the primary
  action is reachable without scrolling at all, not just indicated as
  scrollable. Measured at 844x390 with `body.touch-ui` (the real mobile
  sizing) applied: `Start Game` bottom edge at 248px, well inside the
  390px viewport (was cut in half per the task's own screenshot; an
  intermediate version of this fix that only added `--ui-top-offset`
  without the media query measured 415px, i.e. still 25px past the fold --
  caught before commit, not shipped). Screenshot:
  `t61_phone_landscape_touchui.png`.

**Item 5 (panels indistinguishable).** Each of Help/Scores/Shop/Online now
has a leading icon in its `<h2>` and a `.help-panel-{scores,shop,online}`
modifier class carrying a border-tint + heading colour pulled from that
panel's own existing UI colour elsewhere (gold for Scores' `.hs-new-best`,
green for Shop's `.shop-buy-btn`, blue for Online's account of buttons);
Help keeps the original teal untouched as the baseline. Screenshots of all
four confirm each is identifiable without reading the heading text:
`t61_panel_help.png` (teal, ❓), `t61_panel_scores.png` (gold, 🏆),
`t61_panel_shop.png` (green, 🧬), `t61_panel_online.png` (blue, 🌐).

**Item 6a (P3/P4 cards in a 1v1).** `controlCardsHtml()` gained a
`hideInactive` parameter; `renderControlSplash()` (the live in-game menu)
passes `true`, `renderHelpPanel()`'s static 4-player reference guide passes
nothing (unchanged, still shows all 4 dimmed-if-inactive, since it documents
every possible mapping regardless of the selected mode). Verified: 2
players configured -> 2 splash cards; 4 players configured -> 4 splash cards;
Help panel still shows 4 regardless.

**Item 6b (duplicate close button).** Removed `#uiCloseBtn` (the `&#10005;`
inside `#ui`) entirely -- it called the exact same `togglePauseMenu()` as
`#pauseMenuBtn` (`&#9776;`, always on screen, top-right), so it was a pure
duplicate. The four modal overlays keep their own `.ui-close-btn` close
buttons (confirmed via grep: exactly 4 remain, all on Help/Scores/Shop/
Online) since `#pauseMenuBtn` only toggles `#ui`, not those.

**Item 6c (stray "Survival Time: 0.0s").** The static HTML default for
`#scoreboard` is now empty; `updateUI()` no longer writes the placeholder
text for the solo-mode pre-round case (the multiplayer win-tally text,
which is real information, is untouched). Verified: a fresh page load with
no round ever started shows a blank scoreboard, not "Survival Time: 0.0s"
(`t61_phone_portrait_touchui.png`).

**Regression sweep (item 9/10).** `checkCollision`/`checkArcCollision`/
`raycast`/`rebuildSpatialGrid`/`TRACE_HITBOX`/`NUCLEUS_RADIUS`/
`EFFECT_DURATION`/`GAP_DISTANCE`/any hit-cooldown constant do not appear
anywhere in the diff (confirmed by grep over `git diff`), so AGENT_CONDUCT
§4.1/§7.6 don't strictly apply -- this is a layout-only task. Still ran the
sweep for real: forced a membrane death (teleport just past
`activeCell.radiusX`) at all three speeds (Normal/Fast/Very Fast) with a
real round in progress -- death fired correctly every time
(`alive0: false`, `isPlaying: false`) and the new round-over UI rendered
clean with 0 console errors at each speed
(`t61_regress_Normal.png`/`Fast`/`VeryFast`). A real unpiloted 30.2s round (1
player + 3 bots) played normally throughout, including opening/closing the
pause menu and the control splash mid-round: `worldChildren` flat at 16,
6621 trace points, 0 console errors.

**Verified over `file://`.** Both the source `260703_Cellsnake.html` and the
rebuilt `dist/Cellular_Zatacka.html` (the fully self-contained standalone,
which is what a player without a folder actually runs) load and start a
round cleanly offline, 0 console/page errors either way.

`sw.js` `CACHE_NAME` bumped v40→v41; `dist/` rebuilt (`--check` passes).
