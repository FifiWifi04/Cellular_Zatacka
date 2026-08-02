# T10 — Dev hotkey alignment + on-screen legend

**Track:** B · **Depends on:** T04 · **Risk:** very low · **Est. diff:** ~40 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Make the dev hotkeys match what `Development_plan.md` documents, keep the existing
keys working, and put a readable legend on screen.

## Why

`Development_plan.md` states:

> Dev Mode Active: `\` toggles god mode, `]` fast-forwards survivalTime by 15s.

The implementation does neither:

- Dev mode toggles on `½`, `` ` ``, or `~`
- `Tab` fast-forwards 15s
- `f` runs the fuzzer

`½` is a Danish/Nordic keyboard key that does not exist on most layouts, and
`Tab` is intercepted with `preventDefault()`, which fights browser focus
handling. Anyone following the roadmap document will conclude dev mode is broken.

After T04 there are three flags to control, so the mapping needs to be explicit
anyway.

---

## Prerequisites

T04 must be done — `devMode`, `godMode`, `fuzzActive` must already be separate.
Read the `keydown` handler and the `devIndicator` element in the HTML head.

---

## Target key map

| Key | Action | Notes |
|---|---|---|
| `\` | toggle **dev mode** (master) | roadmap key |
| `` ` `` / `~` / `½` | toggle **dev mode** | keep as aliases — do not remove working keys |
| `]` | +15s `survivalTime` | roadmap key; requires dev mode |
| `Tab` | +15s `survivalTime` | keep as alias, but see below |
| `g` | toggle **god mode** | requires dev mode |
| `f` | toggle **fuzzer** | requires dev mode |
| `h` | toggle the legend overlay | requires dev mode |

Note the roadmap says `\` toggles *god mode*. In the current architecture `\` is
better as the master dev toggle, with `g` for god mode specifically — otherwise
there is no way to reach the other flags. Implement it that way and **update
`Development_plan.md`** to match, in the same commit, so the document and the code
stop disagreeing. That documentation edit is explicitly in scope for this task.

### The `Tab` problem

`Tab` is in the `preventDefault()` list. Keeping it as an alias is fine, but only
`preventDefault()` it while `devMode` is on — otherwise dev mode being off still
breaks tab-navigation on the page. Make that conditional.

### Player-control collision check

**Before assigning `g`, `f`, or `h`, verify they do not collide with player
controls.** From `startRound()`'s `playerConfigs`:

- P2: `a`/`d`/`s`
- P3: `g`/`j`/`h`  ← **collision: `g` and `h` are Player 3's left and toggle**
- P4: `4`/`6`/`5`

So `g` and `h` are taken. Resolve it by gating dev hotkeys on `devMode` being
**already on** (which `\` alone enables), and additionally requiring that the key
is not consumed as a player control while a round is running. The simplest safe
rule: **when `isPlaying` is true, dev hotkeys other than the master toggle require
a modifier** — e.g. `Shift+G`, `Shift+F`, `Shift+H`. Pick that, or pick keys that
are genuinely free (`,` `.` `/` `;` `'` are all unused). Free keys are simpler —
prefer them, and document whichever you choose.

Verify your final choice against all four `playerConfigs` entries by reading them,
not from this table.

---

## Legend overlay

Replace the current `devIndicator` text with a small fixed-position panel showing:

```
DEV MODE            [\]
  god mode   : ON     [<key>]
  fuzzer     : OFF    [<key>]
  +15 s              []]
  legend             [<key>]

fuzz: rounds 41 · 7m12s · trace 12,480 · children 218 · heap 84MB · err 0
```

Rules:

- Plain HTML/CSS in the existing `devIndicator` div — **no PixiJS objects**, so it
  costs nothing to render and cannot leak.
- Update at most **once per second**, not per frame. Reuse T04's `fuzzStats`
  cadence rather than adding a second timer.
- Hidden entirely when `devMode` is off.
- Monospace, small, top-right, `pointer-events: none`, high `z-index` — match the
  existing element's styling so the diff stays small.

---

## Files touched

- `260703_Cellsnake.html`: `devIndicator` markup + CSS, `keydown` handler, the
  once-per-second HUD update from T04.
- `Development_plan.md`: correct the "Dev Mode Active" line under
  *Critical Constraints & Context* to the implemented map.

---

## Verification

1. Console clean.
2. Every key in the final map works, and every alias still works.
3. **No player-control collision.** Start a 4-player round (`currentMode = 4`).
   With dev mode ON, exercise every player's controls — P3's `g`/`j`/`h` must
   steer P3 and must not toggle god mode or the legend.
4. `Tab` does not break page tab-navigation when dev mode is off.
5. The legend shows correct live flag states; toggling a flag updates it within
   one second.
6. The legend disappears completely when dev mode is off.
7. Frame time with the legend visible is unchanged (it updates 1×/s).
8. `Development_plan.md` now matches the code.

## Definition of done

- [ ] `\` and `]` work as documented
- [ ] All pre-existing keys still work
- [ ] Dev keys verified against all four `playerConfigs` for collisions
- [ ] Legend renders in HTML, updates ≤1×/s, hidden when dev mode is off
- [ ] `Development_plan.md` updated in the same commit
- [ ] `docs/TASKS.md`: T10 → `DONE`
