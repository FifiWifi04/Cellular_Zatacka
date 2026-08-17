# T72 — Generation 5: the body notices

**Track:** N (Phase 9) · **Depends on:** T71, T57 · **Risk:** high (new faction, new targeting) · **Est. diff:** ~250 lines

Scoped in [`PHASE9-LATE-GAME-ARC.md`](../PHASE9-LATE-GAME-ARC.md).

**Gen 5 currently exists and is empty.** Generations advance without a ceiling,
but the largest `genAtLeast()` gate in the codebase is 4 and `massGrowInterval()`
floors from Gen 4 onward — so Gen 5, Gen 6 and Gen 20 are mechanically identical
to Gen 4. A player who survives is told they advanced and given nothing. This is
the first task that changes that.

---

## The idea

The cell turned cancerous at Gen 4. Now **the immune system arrives**.

Immune cells enter **through the membrane, from outside** — the one direction
nothing has ever come from in this game. Everything to date spawns inside the
arena or is already part of it.

## Why this one, and why now

- **It reuses T57.** The nucleus chasers are already the game's first entity that
  pursues the player: spawn timer, cap, lifetime, homing, both collision paths,
  red-mode interaction. Immune cells are that machinery with different targeting.
  Most of the cost is paid.
- **It introduces the first non-hostile faction, and that is the new verb.**

## The mechanic: baiting

Immune cells hunt **the nucleus and its chasers as well as the player**. So the
player can lead one into the thing chasing them and let the two fight.

That single rule produces three-way pressure out of one new entity type, and it
is a genuinely new decision — every previous hazard could only be avoided or
broken. Make it **discoverable**: the fight between an immune cell and a chaser
must be visible and legible, or players will never find it.

Design notes:

- An immune cell that is engaged with a chaser should be **less dangerous to the
  player** for that moment — that is what makes baiting worth doing rather than
  just adding a second thing to dodge.
- Do **not** make immune cells friendly. They are lethal to the player on
  contact. The fiction is that the player is part of an abnormal cell; the immune
  system is not wrong to be there. That ambiguity is the interesting part and it
  costs nothing to implement.

## Requirements

- **Entry is telegraphed.** They come through the wall — show the breach point
  before the cell arrives, the way T57's transformation announces itself. Reuse
  `warningElement` and the existing freeze/countdown (T60/T65/T67) if the entry
  warrants a pause; if it does not, do not add one.
- **`rebuildSpatialGrid()`, `checkCollision()` AND `raycast()`** (§4.1). A lethal
  homing thing the bot cannot see will look absurd — and T57's Findings note it
  used gameLoop's own inline sweep rather than `checkCollision()`; follow
  whichever pattern T57 actually established and say which.
- **Capped and lifetime-bounded**, like chasers. `IMMUNE_MAX`.
- **Outrunnable**, measured at every speed setting including Very Slow — the same
  test T57 had to pass.
- **Red-mode behaviour decided and consistent with T50's rule.** An immune cell
  is alive, not dead matter, so it should probably *not* be breakable — which
  means it must **look alive** so the player can tell at a glance. State the
  decision.
- **Visually distinct** from chasers (pink, alive), necrotic clusters (grey
  crystalline) and the aggregate (amber lobes). Screenshot all four together.
- **Bots must cope.** 2 minutes at Gen 5, bots should not die instantly and
  should not ignore them.

## Verification

1. Console clean.
2. **Gens 1–4 completely unaffected.**
3. Entry through the membrane is visible and telegraphed; screenshot.
4. **Baiting works and is visible**: stage an immune cell and a chaser in contact
   and show one destroying the other, with the frame sequence. Report how long an
   engagement takes.
5. **Engagement reduces the threat to the player**, per the design — measure it.
6. Both collision paths; head-on at Very Fast under 4× fuzzer dilation, no
   tunnelling; `raycast()` reports them.
7. Outrunnable at every speed setting — table of immune-cell speed vs player speed.
8. Caps hold over 10 minutes at Gen 5; `IMMUNE_MAX` never exceeded.
9. Bot survival at Gen 5 over 5 rounds — mean time, and no repeated deaths to the
   same immune cell.
10. Visually distinct — one screenshot containing an immune cell, a chaser, a
    necrotic cluster and the aggregate.
11. `worldChildren` flat over 10 minutes; destroyed cells release their sprites.
12. Help panel updated.
13. Regression sweep §7.6.

## Definition of done

- [ ] Immune cells enter through the membrane, telegraphed
- [ ] They hunt the player **and** the nucleus/chasers; baiting demonstrated
- [ ] In `spatialGrid`, and both physics and sensor paths per T57's pattern
- [ ] Capped, lifetime-bounded, outrunnable at every speed
- [ ] Red-mode decision stated and consistent with T50
- [ ] Visually distinct from all three existing hazard families
- [ ] Bots cope; no leak
- [ ] `docs/TASKS.md`: T72 → `DONE`, T73 → `READY`

---

## Findings

*(Targeting model; engagement duration and threat reduction; speed table; bot
survival; the four-hazard screenshot.)*
