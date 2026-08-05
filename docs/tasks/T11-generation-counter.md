# T11 — Generation counter infrastructure

**Track:** C · **Depends on:** T06a · **Risk:** low · **Est. diff:** ~60 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Introduce `activeCell.generation` and the plumbing every Phase 3 mechanic gates
on. **This task adds no gameplay content** — it adds the counter, the increment,
the reset, the display, and a dev control for it.

## Why

`Development_plan.md` Phase 3 says:

> *Wrap all Phase 3 mechanics in conditional gating: `if (activeCell.generation >= X)`*

No such field exists. T12–T15 all depend on it, and if each of them invents its
own version the four mechanics will disagree about what generation it is. Build it
once, first.

---

## Prerequisites

Read: the `activeCell` declaration, `startRound()`, `generateMap()`, and
`updateMitosis()` in full — particularly how the mitosis event ends and how
`activeCell` relates to `mitosis.cellB`.

**The key design question you must answer by reading the code:** what happens at
the end of a mitosis event? Does `activeCell` get replaced by `cellB`, do its
coordinates move, or does the round simply continue in the same cell? Write your
finding into this task file under `## Findings` before implementing — the
increment point depends entirely on the answer.

---

## Design

### The field

```
let activeCell = { x: 1500, y: 1500, radiusX: 1400, radiusY: 1200, radius: 1400, generation: 1 };
```

Generation **1** is the starting state, so `generation >= 2` gates the first new
mechanic — matching how the roadmap numbers them ("Generation 2 — Membrane
Calcification").

### Increment

Increment by exactly one when a mitosis event **completes** — i.e. when the cell
has finished dividing and play continues in the daughter cell. Find that moment
in `updateMitosis()` (look for where `mitosis.state` returns to `'idle'` after
`'narrowing'`, and where `mitosis.nextTriggerTime` is re-armed).

Guard it so it can fire only once per event: set a flag on the `mitosis` object
(`mitosis.generationCounted`) cleared when a new event starts.

### Reset

`startRound()` must reset `activeCell.generation = 1`. Confirm it is not reset
anywhere else, and that `generateMap()` does **not** touch it (a mid-round map
regeneration must not roll the generation back).

### Display

Show the generation in the scoreboard alongside the survival timer, e.g.
`Survival Time: 84.3s · Gen 2`. Find every place `scoreText.innerText` is written
(there are several, including the game-over strings) and keep them consistent.

### Dev control

Add to the dev hotkeys (coordinate with T10 if it has landed; if not, pick a free
key and note it): a key that increments `activeCell.generation` by 1 without
running a mitosis event. Phase 3 content is otherwise untestable — you would have
to survive four full 4-minute mitosis cycles to see Gen 4.

Also expose `window.setGeneration = n => { activeCell.generation = n; }` so the
headless driver can jump straight to a generation.

### A gating helper

Add one helper so T12–T15 all gate identically:

```
function genAtLeast(n) { return activeCell.generation >= n; }
```

Every Phase 3 mechanic must call this rather than reading the field directly. It
gives one place to add future conditions (e.g. "not during the mitosis reveal").

---

## What this task must NOT do

- No membrane shrinking, no organelle freezing, no tumour, no gravity well.
- No change to mitosis timing or behaviour beyond the counter itself.
- No balance changes.

If the counter alone changes how the game plays, something is wrong.

---

## Files touched

`260703_Cellsnake.html` only: `activeCell` literal, `updateMitosis()` increment +
flag, `startRound()` reset, scoreboard strings, `genAtLeast()`, one dev hotkey,
`window.setGeneration`.

---

## Verification

1. Console clean.
2. **Starts at 1.** New round shows `Gen 1`.
3. **Increments once per mitosis.** Fast-forward through a full mitosis event.
   The display must go 1 → 2 exactly once — not twice, not every frame. Watch it
   through the whole event including the narrowing phase and the snap.
4. **Survives a second event.** Fast-forward through two consecutive mitosis
   events; the display must reach `Gen 3`.
5. **Resets on restart.** Restart the round; back to `Gen 1`.
6. **Not reset mid-round.** If anything calls `generateMap()` mid-round, the
   generation must be unaffected. Find out whether that happens by searching for
   `generateMap(` call sites.
7. **Dev control works.** The hotkey and `window.setGeneration(4)` both move the
   display.
8. **No behaviour change.** Play a full round at Gen 3 via the dev control. The
   game must play exactly as it did before this task — nothing is gated yet.

## Definition of done

- [ ] `## Findings` section filled in above, describing what happens at the end
      of a mitosis event
- [ ] `activeCell.generation` exists, starts at 1, increments once per completed
      mitosis, resets on `startRound()`
- [ ] `genAtLeast(n)` helper added
- [ ] Dev hotkey + `window.setGeneration` available
- [ ] Generation visible in the scoreboard in all its states
- [ ] Zero gameplay change demonstrated
- [ ] `docs/TASKS.md`: T11 → `DONE`; T12, T13, T14, T15 → `READY`

---

## Findings

At the end of a mitosis event ("THE SNAP", `timeInEvent >= 120` inside
`updateMitosis()`), the round does **not** switch to `mitosis.cellB` as a
separate object — `activeCell.x`/`activeCell.y` are overwritten in place with
`mitosis.cellB`'s coordinates (`activeCell.x = mitosis.cellB.x; activeCell.y =
mitosis.cellB.y;`). `activeCell.radiusX/radiusY/radius` are untouched (both
cells are always the same size), `generateMap(true)` is then called to redraw
the nucleus/ER/Golgi at the new location, and surviving vesicles/viruses/
organelles are re-parented into the same `activeCell`. There is no swap of the
whole `activeCell` object and no second `activeCell`-shaped variable — one
`activeCell` object is mutated in place, once per completed event, right
before `mitosis.state` is reset to `'idle'` and `mitosis.nextTriggerTime` is
re-armed.

The increment was placed in that exact spot: immediately after
`mitosisLayer.clear()` and before `mitosis.state = 'idle'`, guarded by
`mitosis.generationCounted` (set back to `false` when a new event starts, at
`mitosis.state = 'forming'`). This runs exactly once per snap because the
`if (timeInEvent >= 120)` block itself only executes while
`mitosis.state !== 'idle'`, and it flips `mitosis.state` to `'idle'` inside
the same execution — but the flag is kept anyway as the belt-and-suspenders
guard the task asked for, in case that timer-gating logic ever changes.

Also confirmed via `generateMap(` call-site search: it is called at line 695
(definition), inside the snap (`generateMap(true)`, mid-round, must not touch
generation), in `startRound()` (fresh round, generation already reset
separately), and once at module scope on page load (before any round exists).
None of those sites read or write `activeCell.generation`, so a mid-round
`generateMap()` call cannot roll the counter back.
