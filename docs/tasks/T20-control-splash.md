# T20 — Control-mapping splash screen

**Track:** E · **Depends on:** — (independent, can be taken any time) · **Risk:** very low · **Est. diff:** ~90 lines

Read `docs/AGENT_CONDUCT.md` before starting. This is the safest task on the
board — a good one to take when the head of every other track is blocked.

---

## Goal

A clean, scannable splash screen showing the input keys for Players 1 through 4.

Roadmap 5.2:

> Build a clean, scannable control-mapping splash screen displaying input keys for
> Players 1 through 4.

---

## Why it matters more than it looks

The controls are currently communicated by a single line of text
(`<h3 id="controlsText">P1 (Blue): Left/Right Arrows</h3>`) that only describes
the players currently selected. A local 4-player game with keys spread across
`arrows`, `a/d/s`, `g/j/h`, and `4/6/5` is unlearnable from one line — and the
`targetMode` toggle key is the least discoverable mechanic in the game.

---

## Source of truth

**Read the control map from `playerConfigs` in `startRound()`. Do not hard-code
it in the HTML.** If they are duplicated they will drift, and the splash will lie.

The current map, for reference only — verify against the code:

| P | Colour | Left | Right | Toggle |
|---|---|---|---|---|
| 1 | Blue | `ArrowLeft` | `ArrowRight` | `ArrowDown` |
| 2 | Red | `a` / `A` | `d` / `D` | `s` / `S` |
| 3 | Green | `g` / `G` | `j` / `J` | `h` / `H` |
| 4 | Yellow | `4` | `6` | `5` |

`playerConfigs` is currently declared **inside** `startRound()`, so it is not
reachable from the splash code. Hoist it to module scope, next to the other
game-state declarations, and have `startRound()` read the hoisted constant.
That is a small, safe move — but check nothing else shadows the name, and confirm
`startRound()` does not mutate the config objects (if it does, hoisting would let
mutations leak across rounds — in that case deep-copy at use).

Render the key names through a small display-name map so `ArrowLeft` shows as
`←`, `ArrowDown` as `↓`, and letters show uppercase.

---

## Design

### Layout

Four cards in a responsive row (wrapping to 2×2 on narrow windows), one per
player:

```
┌────────────────────┐
│ ● PLAYER 1   Blue  │
│                    │
│   ←   turn left    │
│   →   turn right   │
│   ↓   toggle mode  │
└────────────────────┘
```

- The bullet takes the player's actual colour from `playerConfigs[i].color`
  (convert the hex number to CSS with `'#' + color.toString(16).padStart(6,'0')`).
- Keys rendered as `<kbd>`-style chips — bordered, monospace, clearly keys.
- Cards for players not in the current configuration are dimmed, not hidden, so
  the full map is always learnable.

Add one short line under the cards explaining what the toggle actually does —
`self` (green aura, collect vesicles) vs `attack` (red aura, shatter structures).
Two sentences, no more. This is the mechanic nobody discovers.

### Where it lives

Plain HTML/CSS in the existing `#ui` panel — **no PixiJS**. Keep it inside the
menu so it appears on the landing screen and after a round ends.

Add a `Controls` toggle button in `.controls` that shows/hides it, plus a
keyboard shortcut (`c` — but **verify against `playerConfigs` first**; if `c` is
ever a player key, pick another, and guard it on `!isPlaying` regardless).

Default: visible on first load, remembered within the session via a module-level
boolean. Do not use `localStorage` — the game must work from `file://` where
storage behaviour varies.

### Keep the existing line

`#controlsText` is updated by `updateUI()`. Leave it working; the splash
supplements it. If the splash makes it redundant once you see them together, say
so in `docs/BACKLOG.md` rather than deleting it here.

---

## Files touched

`260703_Cellsnake.html` only: hoist `playerConfigs`, new splash markup + CSS, a
render function called from `updateUI()`, a toggle button and hotkey.

---

## Verification

1. Console clean.
2. **Accuracy.** Every key shown must actually work. Start a 4-player round and
   test all twelve bindings against the splash.
3. **Single source of truth.** Change a key in `playerConfigs` (temporarily) and
   confirm the splash updates without any other edit. Revert the change.
4. **Colours match.** Each card's colour dot matches that player's in-game trace
   colour.
5. **Dimming.** With 2 players selected, cards 3 and 4 are dimmed but readable.
6. **Responsive.** Check 1280×1024, a narrow window (~600px), and fullscreen.
   Cards wrap cleanly; nothing overflows.
7. **Toggle** button and hotkey both work, and the hotkey does nothing mid-round.
8. **No PixiJS objects added.** `worldChildren` unchanged.
9. **Round flow.** The splash appears on the landing screen, hides when a round
   starts, and reappears on the game-over screen.

## Definition of done

- [ ] `playerConfigs` hoisted to module scope and used as the only source
- [ ] Four cards, real colours, real keys, arrow glyphs for arrow keys
- [ ] Toggle-mode explanation included
- [ ] Inactive players dimmed, not hidden
- [ ] Responsive at three widths
- [ ] Pure HTML/CSS, no PixiJS, no `localStorage`
- [ ] `docs/TASKS.md`: T20 → `DONE`
