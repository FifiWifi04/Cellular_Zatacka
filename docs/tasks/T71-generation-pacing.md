# T71 — Advance generations on what the player did, not on the clock

**Track:** N (Phase 9) · **Depends on:** T52 · **Risk:** medium-high (changes the whole run's shape) · **Est. diff:** ~90 lines

Scoped in [`PHASE9-LATE-GAME-ARC.md`](../PHASE9-LATE-GAME-ARC.md). **Do this
before T72.** Gen 5 content placed behind a twenty-minute wall is content nobody
sees.

---

## The problem

Generations advance on `MITOSIS_INTERVAL = 240` — one every four minutes,
regardless of anything the player does. So Gen 4 arrives at roughly **twelve
minutes**, and Gen 6 would land around **twenty**.

Two consequences, and the second is the worse one:

1. Late content is effectively unreachable.
2. **Survival time rewards turtling.** The optimal play for reaching a new
   generation is to hug a safe corner and wait, because the clock does not care
   what you did.

## The fix

Advance on the **nucleus feed meter** (T52) rather than the clock. The meter
already rises when the nucleus consumes a vesicle and falls behind when the
player intercepts, so:

- A player who actively denies the nucleus **slows the ladder**.
- A player who hides lets it fill and gets pushed forward.
- T51's ATP granules and T52's interception window become genuinely
  consequential rather than local optimisations.

That is the recommendation in the phase doc. The fallback, if this proves
unworkable, is simply to shorten `MITOSIS_INTERVAL` as generations rise — say so
in `## Findings` if you take it, and why.

### The problem you have to solve

**The feed meter only exists from Gen 4** (`genAtLeast(4)` gates the well). Gens
1→2, 2→3 and 3→4 have no meter to advance on. Options:

- **(a) Generalise the meter.** Make it accumulate from Gen 1, with the well and
  the HUD bar still only appearing at Gen 4. The nucleus is "always feeding"; it
  simply becomes visible later. Cleanest fiction, most code.
- **(b) Hybrid.** Clock for 1→4 with a shortened interval, meter from 4 onward
  where the mechanic exists. Smallest diff, but two rules the player must learn.
- **(c) A per-generation progress source** — something already counted at each
  generation (vesicles collected, distance, breaks). Risks rewarding grinding.

**Recommended: (a).** It gives one rule for the whole run and makes the Gen 4 HUD
bar a *reveal* of something that was already true, which is a nicer moment than
a new mechanic appearing from nowhere.

### Non-negotiables

- **The bar must be visible whenever it is driving progression.** If the meter
  advances generations from Gen 1, the player sees it from Gen 1. A hidden
  progression driver is the T13 mistake again.
- **Mitosis stays the vehicle.** The generation still advances *through* a
  division — this task changes what schedules it, not what happens. Do not
  bypass `MITOSIS_INTERVAL`'s event; retarget it.
- **A round must still be able to end.** Verify a passive player still reaches
  Gen 2 in reasonable time; if hiding stalls the ladder completely, the design
  has inverted the problem rather than fixed it.
- **Online (T30) syncs generation state.** Whatever drives it must be on the
  host's authoritative side, not computed per client.

## Verification

1. Console clean.
2. **Time to each generation, measured**, for three play styles over full runs:
   a passive player, a bot-average player, and an actively-collecting player.
   Report a table. Gen 4 must arrive materially sooner than twelve minutes for
   the active player.
3. **Denial visibly slows the ladder** — the active player reaches Gen 5 *later*
   than the passive one, which is the whole point. If it does not, the coupling
   is not working.
4. Passive play still advances: a parked player still reaches Gen 2, and the
   round still ends.
5. Bar visible whenever it drives progression; screenshot at Gen 1 and Gen 4.
6. Mitosis still the vehicle — the division event still fires and still moves the
   player to Cell B.
7. Online: generation advances identically on host and client over a 2-minute
   local relay session, or state clearly that online was not exercised and why.
8. `worldChildren` flat; no leak.
9. Regression sweep §7.6.

## Definition of done

- [ ] Option chosen with reasoning; fallback stated if taken
- [ ] Generation driven by the meter, mitosis still the vehicle
- [ ] Time-to-generation table for three play styles
- [ ] Denial proven to slow the ladder
- [ ] Passive play still advances and still ends
- [ ] Bar visible wherever it drives progression
- [ ] `docs/TASKS.md`: T71 → `DONE`, T72 → `READY`

---

## Findings

*(Option and why; the time-to-generation table; the denial comparison.)*
