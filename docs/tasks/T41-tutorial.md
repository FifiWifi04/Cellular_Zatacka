# T41 — How-to-play tutorial

**Track:** K · **Depends on:** T36, T40 · **Risk:** low · **Est. diff:** large but self-contained

Read `docs/AGENT_CONDUCT.md`.

## The gap

> "There needs to be a tutorial with explanation of the game and how it works,
> different boosts, etc."

Nothing currently explains the vesicle economy, target modes, the mitosis event,
the infection warning, or the generation ladder. A new player sees a glowing cell
and dies.

**Depends on T36** because the target-mode rules are being fixed there — do not
document behaviour that is about to change.

## Scope: a static illustrated guide, not an interactive walkthrough

An interactive tutorial level is a much larger project and would need its own
scripted state machine. Build the **explanation** first; log "interactive
tutorial" in `docs/BACKLOG.md` if it still seems wanted afterwards.

Deliver a **Help / How to Play** panel, reachable from the menu and from the
pause menu (T40), covering:

1. **Goal** — survive, do not touch anything lethal, outlast the others.
2. **Controls** — reuse T20's control splash rather than duplicating it.
3. **What kills you** — membrane, your own and others' traces, organelles,
   the nucleus, microtubules during mitosis, virus particles, the Gen 3 growth.
   Show each with a small colour swatch or icon matching its in-game appearance.
4. **Vesicles** — one line per cargo type: what it looks like, what it grants,
   how long it lasts. Read the actual effect constants; do not guess.
5. **Target mode** — green vs red, stated exactly as T36 implements it.
6. **Events** — the infection warning, and mitosis (bridge, microtubules,
   the sweep, reaching Cell B).
7. **Generations** — what changes at Gen 2, 3 and 4, one line each.

## Build it as HTML, from the data

Plain HTML/CSS in the existing UI, no PixiJS. Where a value is a constant in the
code (effect durations, generation thresholds, growth intervals), **read it from
the constant** rather than hard-coding the number into prose, so the guide cannot
drift from the game the way the control legend did.

Scrollable, `max-height: 90dvh`, touch-friendly targets per T24, closable.

## Verification

1. Console clean.
2. Every stated fact checked against the code — especially effect durations and
   generation thresholds.
3. Reachable from both the main menu and the pause menu.
4. Readable at 1280×1024, at 390×844 portrait, and in landscape on a short
   screen.
5. Opening it mid-round pauses; closing resumes.
6. No PixiJS objects added — `worldChildren` unchanged.
