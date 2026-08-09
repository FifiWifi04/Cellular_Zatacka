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

- [ ] New pickup array, Gen 2+, spawn-biased to the annulus being lost
- [ ] One effect chosen, bounded, with the reasoning in `## Findings`
- [ ] Membrane feedback + HUD readout + pickup burst
- [ ] Bots see and collect them
- [ ] Generation still ends under active collection — proven over 10 minutes
- [ ] Help panel updated from live constants
- [ ] `docs/TASKS.md`: T51 → `DONE`

---

## Findings

*(Effect chosen and why; radius-vs-time across a pickup; the caps; bot pickup
rate; the 10-minute proof that the wall still closes.)*
