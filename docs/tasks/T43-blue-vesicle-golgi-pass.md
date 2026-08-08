# T43 — The blue vesicle's Golgi-pass effect does nothing

**Track:** J · **Depends on:** — · **Risk:** medium (gameplay) · **Priority: high**

Read `docs/AGENT_CONDUCT.md`.

## The bug (owner playtest)

> "The blue vesicle boost does not work. Originally it allowed you to go through
> the Golgi, now I was killed when it happened."

## Cause — `golgiTimer` is granted, displayed, and never read

Collecting a `membrane` (blue) vesicle grants:

```
target.effects.golgiTimer = Math.min(15.0, target.effects.golgiTimer + EFFECT_DURATION);
```

`golgiTimer` is then decremented each frame and drawn as a HUD bar — and that is
**everything it does**. Grep the whole file: there is no read of `golgiTimer` in
`checkCollision()`, `checkArcCollision()`, `raycast()`, or any other gameplay
path. It is a countdown that renders a progress bar and grants nothing.

`git log -S golgiTimer` returns only `4bf057f`, the initial import — so it has
**never** been wired up in this repository's history. The owner's memory of it
working predates the repo.

Note what *does* work: three blue pickups inside the combo window grant
`ghostTimer = 10.0`, and ghost genuinely bypasses everything (`checkCollision()`
returns `false` early for it). So blue is not entirely dead — the **single-pickup
Golgi pass is**, which is exactly the case the owner hit.

### A second, compounding cause

T36's `boostTarget(p)` routes a pickup to the nearest opponent when the collector
is in `attack` (red) mode. So picking up blue while red hands the whole effect
away — correct per T36, but combined with the dead timer it makes blue feel
completely broken. Worth confirming which of the two the owner actually hit;
both need to be true for "nothing happened at all".

## Fix

Make `golgiTimer` mean what the game already implies: **while it is active, the
player passes through the ER/Golgi walls, and nothing else.**

- In `checkCollision()`, skip `checkArcCollision()` when
  `player.effects.golgiTimer > 0`. Place it *after* the membrane and nucleus
  checks and *before* the arc check — mirroring exactly how the ghost bypass is
  positioned, so the two read the same way.
- **Both paths (§4.1).** `raycast()` must also stop reporting `'wall'` hits for a
  caster with an active `golgiTimer`, or the bot will keep avoiding walls it can
  now drive through. `raycast()` already takes `casterId`; look the player up
  once, as T01 does.
- Do **not** make it bypass anything else — not traces, not organelles, not the
  membrane. That is ghost's job, and the distinction is what makes the two
  pickups different.

### Make it legible

The player must be able to see the effect is active, and the HUD bar alone
clearly was not enough. Add a visible cue on the ER/Golgi arcs themselves while
any local player has `golgiTimer > 0` — a dimming or a dashed/ghosted outline
saying "this is not solid for you right now". Keep it cheap: the arcs already
redraw through `drawArcs()`.

## Verification

1. Console clean.
2. **The headline test.** Collect one blue vesicle in green/self mode, drive
   straight into an ER or Golgi arc. You pass through. Drive into it again after
   the timer expires: you die.
3. **Only the arcs.** With `golgiTimer` active, confirm you still die to the
   membrane, your own trace, an organelle, and the nucleus. It must not be a
   second ghost mode.
4. **Bot agrees.** With the timer active on a bot, log `raycast()` results and
   confirm no `'wall'` hits are reported. Watch a bot for 60s and confirm it will
   now cross the arcs while boosted instead of steering around them.
5. **Red mode.** In attack mode the pickup goes to the nearest opponent (T36) —
   confirm the *opponent* gains the pass and the collector does not. Solo, it
   falls back to self.
6. **The 3× ghost combo still works** and still bypasses everything.
7. **Visual cue** appears and disappears with the timer.
8. Regression sweep §7.6.

## Definition of done

- [x] `golgiTimer` skips `checkArcCollision()` and nothing else
- [x] `raycast()` suppresses `'wall'` for a boosted caster — both paths agree
- [x] Visual cue on the arcs while active
- [x] Ghost combo unaffected
- [x] `docs/TASKS.md`: T43 → `DONE`

## Progress notes (verification, 2026-08-08)

Implementation:
- `checkCollision()`: `if (player.effects.golgiTimer <= 0 && checkArcCollision(x, y, player)) return true;`
  — replaces the unconditional call, placed exactly where it was (after the
  membrane/nucleus/ghost checks). `checkArcCollision()` itself is untouched.
- `raycast()`: the ER/Golgi analytic pre-pass is now gated
  `if (centralHitboxes.length > 0 && !(caster !== null && caster.effects.golgiTimer > 0))`,
  using the `caster` lookup that already existed for `isOwnNeck`.
- Visual cue: `rotatingContainer.alpha` is set once per frame (inside the
  existing `!isCellFrozen` block, no new allocation) to `0.35` when any
  `!p.isBot` player has `golgiTimer > 0`, else `1.0`. No `drawArcs()` redraw
  needed — this is the same container T09/T33 already own.

Verified via `tools/verify_harness.py` (direct function calls through
`page.evaluate`, plus one real-time bot-watch and two screenshots):
- Headline test: `checkArcCollision()` still returns `true` at a wall point
  regardless of `golgiTimer` (unchanged), but `checkCollision()` flips
  `true` → `false` for the same point solely based on `golgiTimer` state.
- Only the arcs: with `golgiTimer` active, `isOutsideCell`/`isInsideNucleus`
  and `checkCollision` against an organelle and another player's trace all
  still return lethal `true`.
- Bot agrees: 20 samples of `raycast()` on a live bot over 60 game-seconds
  with `golgiTimer` kept topped up returned `'clear'` every time, zero
  `'wall'` hits (would have been `'wall'` at ~8px range before the fix, per
  the same-point no-timer control in the headline test).
- Red mode: collector in `targetMode:'attack'` picks up a blue vesicle —
  opponent's `golgiTimer` goes 0 → 7 (EFFECT_DURATION), collector's stays 0.
- 3× ghost combo: three blue pickups in-window still set `ghostTimer = 10`
  on the third, and ghost still bypasses an organelle collision afterward
  (`checkCollision` → `false`), unaffected by this change.
- Visual cue: `rotatingContainer.alpha` reads `1.0` with `golgiTimer = 0` and
  `0.35` with `golgiTimer > 0` after one `gameLoop` tick; confirmed visually
  in screenshots (`/tmp/verify/t43_golgi_inactive.png`,
  `t43_golgi_active.png`) — the ER teal line and red ribosome dots visibly
  dim when active.
- Regression sweep across all three speeds (1.5/2.5/3.5): membrane,
  organelle and ER/Golgi-wall collisions with `golgiTimer = 0` (the default
  all round) are all still lethal at every speed. One anomaly found at
  Very Fast (3.5) unrelated to this change — see `docs/BACKLOG.md`
  "Found while doing T43".
- Console clean throughout (dev server + `assert_console_clean()`).
- `python3 tools/build_standalone.py --check` passes; `sw.js` `CACHE_NAME`
  bumped v6 → v7.
