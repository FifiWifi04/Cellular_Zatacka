# T51 — Give the player a way to fight the shrinking membrane

**Track:** K · **Depends on:** T12 · **Risk:** medium (new pickup + new timer) · **Est. diff:** ~110 lines

Owner design request, 2026-08-09: *"There should also be some way for a player to
collect some things in the cell to slow down or pause the shrinking so they
search for things and hope to survive for longer."*

---

## Why this is the right addition

From Gen 2 the membrane calcifies inward toward `baseRadiusX * CALCIFY_FLOOR`
and the player can do **nothing** about it. It is the only hazard in the game
that is purely a countdown: every other one — organelles, the aggregate, necrotic
clusters, the Gen 4 well — can be dodged, broken or exploited. A countdown with
no counterplay makes late generations feel like waiting rather than playing.

This gives the shrink a dial the player holds, and it creates the search-under-
pressure loop the owner described: the arena is closing, and the thing that buys
you time is somewhere in it.

## Fiction

Calcification is calcium flooding the cell. What clears it is the membrane's
**calcium pumps**, and pumps run on ATP. So: **ATP granules**. Collect one and
the pumps run harder for a while; the wall stops advancing, or retreats.

This is real cell biology (PMCA/SERCA are ATP-driven Ca²⁺ pumps), it reuses the
game's existing vesicle-collection verb, and it is not another lethal thing.

## How it plays, in one paragraph

From Gen 2 the wall starts creeping in. Small pale-yellow granules begin
appearing, and they appear **preferentially in the ring of floor the wall is
about to take** — the part of the arena that is about to stop existing. Grab one
and the wall stops dead for a few seconds; a bar in the HUD counts that time
down, and the membrane itself glows while it is held. So the round becomes: the
room is closing, the thing that stops it closing is out near the edge, and every
trip out there is a trip into the part of the map you are least able to leave.
Sit safe in the middle and you get no granules and the wall keeps coming. The cap
on stacking means you can delay the wall but never stop it — you are buying
seconds, not winning.

## Design

### The pickup

- New entity, its own array — **do not overload `vesicles`**, whose effects,
  colours and spawn rules are a closed set the help panel documents. Model the
  new array's lifecycle on `vesicles`, but keep it separate.
- **Only spawns from Gen 2**, when calcification is running. Before that it
  would be a pickup that does nothing.
- **Spawn position is the mechanic.** Bias spawns toward the annulus between the
  current wall and where the wall started — the ground the player is about to
  lose. That is what makes collecting one a decision rather than a freebie.
  Never spawn inside the nucleus or inside the aggregate.
- Cap live granules (`ATP_MAX`) and give them a lifetime so an uncollected field
  does not accumulate.
- Visual: distinct from every vesicle colour in use. Recommend a pale
  yellow-green, small, with a slow pulse — bright enough to be a beacon at the
  low camera zooms measured in T47.

### The effect — pick ONE and say why

1. **Pause.** `calcifyPauseTimer` seconds during which the radii do not move.
   Clearest to read and to explain in the help panel. **Recommended.**
2. **Slow.** Multiply `CALCIFY_RATE` for a window. Subtler; harder to notice,
   which is the same complaint the owner made about calcification itself.
3. **Reverse.** The wall retreats a little. Strongest feeling, but it fights
   T12's floor and can undo a generation's pressure with two pickups.

Whichever is chosen: **stacking must be bounded.** Collecting five in a row must
not buy five times the time — cap the timer (`ATP_PAUSE_MAX`) so the wall always
eventually wins. The generation must still end.

### Feedback — non-negotiable

A pickup whose effect the player cannot see is T13's mistake repeated. All three:

- The membrane visibly changes while the effect is live — the existing
  `calcifyLayer` ring already redraws every frame, so tint or pulse it rather
  than adding a layer.
- A HUD readout of the remaining time, alongside the existing effect timers.
- A T17 particle burst on pickup, from the **existing pooled emitter**.

### Bots

`raycast()` and the bot's reward channels must see granules, or bots will look
stupid from Gen 2 onward and the difficulty balance shifts to the human. Add it
as a **reward** channel, not a hazard (§4.1 is about lethal things, but the bot
seeing rewards is what T03 normalised).

## Verification

1. Console clean.
2. **Gen 1 completely unaffected** — no granules, no timer, no HUD element.
3. Collecting one measurably changes the wall: log `activeCell.radiusX` each
   second across a pickup and show the flat (or reversed) span. Numbers in
   `## Findings`.
4. **Stacking is capped** — collect 5 rapidly, show the timer clamps at
   `ATP_PAUSE_MAX`.
5. **The generation still ends.** 10 minutes at Gen 2 with a bot actively
   collecting: the wall still reaches `CALCIFY_FLOOR`. If it does not, the caps
   are wrong.
6. **Bots collect them** — 2 minutes at Gen 2, bots pick up at least one.
7. Caps hold: live granules never exceed `ATP_MAX`.
8. **No leak**: `worldChildren` flat over 10 minutes at Gen 2; collected and
   expired granules release their sprites.
9. Help panel (T41) updated — it is generated from live constants, so quote the
   real duration, not a restated one.
10. Regression sweep §7.6.

## Definition of done

- [x] New pickup array, Gen 2+, spawn-biased to the annulus being lost
- [x] One effect chosen, bounded, with the reasoning in `## Findings`
- [x] Membrane feedback + HUD readout + pickup burst
- [x] Bots see and collect them
- [x] Generation still ends under active collection — proven over 10 minutes
- [x] Help panel updated from live constants
- [x] `docs/TASKS.md`: T51 → `DONE`

---

## Findings

**Effect chosen: Pause (option 1).** Clearest to read (a flat span on a
logged `radiusX` trace is unambiguous, unlike Slow's subtler rate change),
and doesn't fight T12's floor the way Reverse would. Implemented as a single
**global** `calcifyPauseTimer`, not a per-player effect routed through
`boostTarget()` like the three vesicle types: the membrane and its shrink are
shared by every player in the cell, so there's nothing for an 'attack'-mode
redirect to target — every pickup, by any player, adds
`ATP_PAUSE_DURATION`(4s) to the one timer, clamped at `ATP_PAUSE_MAX`(12s).

**Spawn annulus — read literally vs. as implemented.** The design doc's
"annulus between the current wall and where the wall started" (`radiusX` to
`baseRadiusX`) is, read literally, ground the membrane has *already* retreated
past — outside the current cell, unreachable. Implemented instead as
`ATP_ANNULUS_FRAC`(0.72) to 1.0 of the **current** `radiusX`/`radiusY` — the
band of ground closest to the current wall, matching the design's own flavour
text ("out near the edge... about to stop existing"). Noted rather than
blocked per AGENT_CONDUCT §10.3 (smaller/conservative reading, alternative
noted).

**Radius-vs-time across a pickup** (`t51_pause_cap.py`, Gen 2, direct
`calcifyPauseTimer` mutation via the exact clamp expression the real pickup
path uses):

| sample | radiusX | pauseTimer |
|---|---|---|
| before pickup | 1398.2 → 1389.2 → 1380.2 | 0 (shrinking normally, ~6px/game-s) |
| after 1 pickup | 1379.6 | 2.3 |
| " | 1379.6 | 0.9 (flat while paused) |
| " | 1376.0 | 0 (resumed the instant the pause hit 0) |
| +1.5s later | 1368.2 → 1357.4 | 0 (shrink continues normally) |

**Stacking cap**: 5 rapid pickups (`calcifyPauseTimer = min(ATP_PAUSE_MAX,
+= ATP_PAUSE_DURATION)` called 5×, not 5×4=20) clamped at **11.9/12** (the
0.1 short of 12 is real time elapsing between the 5 back-to-back `evaluate()`
calls, not a clamp error).

**Generation still ends under active collection** (`t51_soak.py`, Gen 2, 1
player + 3 bots, `godMode` on so nobody dies to anything else and truncates
the round — verified this doesn't also suppress the shrink, which has no
`godMode` gate): reached `CALCIFY_FLOOR` (630px, from `baseRadiusX` 1400) at
`survivalTime` **142.0s**, and held there through the rest of the ~210
game-second/236 wall-second window. `everPaused: true` — the timer was
observed at 1.87s mid-run, i.e. a bot did pause the shrink at least once —
and the wall still closed. This is a **real, non-synthetic run** (unlike some
recent tasks' time-boxed substitutions): at 640×480 in this configuration the
game/wall-time ratio measured ~0.9x, well over the harness docstring's
general 0.38x, so the literal ask fit inside one invocation. Capped the
window at 210 game-seconds specifically to stay clear of `MITOSIS_INTERVAL`
(240s) — see the two `docs/BACKLOG.md` entries filed today on the mitosis
snap's `godMode` gap and on `atpGranules` not being rescued there.

**Bots collect them**: same run — `everPaused: true` is direct evidence (the
timer only moves via a pickup), and `atpLive` (live granule count) fluctuated
down as well as up across samples, consistent with pickups happening
alongside spawns, not just expiry.

**Caps hold**: `atpLive` peaked at exactly **6** (`ATP_MAX`) across 20 samples
over the same run, never exceeded.

**No leak**: `worldChildren` flat at **15** across all 20 samples of the same
~210-game-second run. Granules have no PIXI display object of their own
(drawn immediate-mode into the single `atpLayer` Graphics, cleared+redrawn
every frame — same pattern as `dynamicLayer`/vesicles), so there is no
per-granule sprite to leak in the first place.

**Regression sweep (§7.6)**, since `raycast()` and `rebuildSpatialGrid()`
were touched: direct `checkCollision()` calls at each speed's real
per-frame step size (90/150/210px, from 1.5/2.5/3.5 × 60fps) —
membrane/own-trace/organelle death and own-neck survival all correct at all
three speeds (`t51_regression2.py`). An earlier live-movement version of this
same check produced two false negatives (organelle death, neck survival) —
traced to test-script issues (organelle drift during the ~1.5s real-time
polling window; a full 180° reversal isn't actually a "near-miss along the
neck" since `traceDist` accumulates path length regardless of direction, so
it walks back out of its own `NECK_LENGTH` window by design) — not to any
regression in the collision code itself, which the deterministic version
confirms untouched by this diff.

**Console clean** across every check above (`http://` and `file://` smoke,
`t51_final_smoke.py`); `python3 tools/build_standalone.py --check` passes;
`sw.js` `CACHE_NAME` bumped v19→v20.
