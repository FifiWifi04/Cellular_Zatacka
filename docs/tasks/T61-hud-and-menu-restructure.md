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

- [ ] Single ordered HUD stack; no overlap at any size
- [ ] Legend stated once
- [ ] Round-over and pre-round are distinct states; result is first after a round
- [ ] Phone overflow indicated; primary action above the fold
- [ ] Panels visually distinguishable
- [ ] P3/P4 cards conditional; duplicate close affordance resolved; stray timer hidden
- [ ] `docs/TASKS.md`: T61 → `DONE`

---

## Findings

*(Before/after screenshots at all three sizes for each item.)*
