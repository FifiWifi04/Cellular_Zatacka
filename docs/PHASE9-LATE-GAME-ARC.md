# Phase 9 — What comes after Generation 4

Owner question, 2026-08-09: *"what if people survive Gen 4, what are the future
steps?"*

This is a design note, not a task. **No task files yet, deliberately** — T52 and
T57 build the Gen 4 race and its ending, and how those actually feel to play
determines what should follow. Writing Gen 5 before Gen 4 has been played is how
you get a generation that repeats a beat instead of answering it.

---

## First, the thing that needs saying: Gen 5 currently exists and is empty

Generations advance on a timer — `MITOSIS_INTERVAL = 240`, one per mitosis, and
`activeCell.generation++` has no ceiling. But every hazard is gated by
`genAtLeast(n)` with the largest `n` in the codebase being **4**:

| Gate | What it turns on |
|---|---|
| `genAtLeast(2)` | membrane calcification, organelle necrosis |
| `genAtLeast(3)` | the protein aggregate |
| `genAtLeast(4)` | the angiogenesis well |

The only thing that changes past Gen 4 is `massGrowInterval()`, `max(2, 10 - 2*gen)`,
which **floors at 2 from Gen 4 onward**. So Gen 5, Gen 6 and Gen 20 are
mechanically identical to Gen 4. A player who survives is told they have advanced
and then given nothing.

That is the real answer to the question today: nothing happens. Which is why it
is worth planning.

## The arc so far, and where it points

The generations track a coherent biological story, and it is worth naming because
it makes the next beat obvious:

| Gen | Biology | Feeling |
|---|---|---|
| 1 | healthy cell | learn the space |
| 2 | calcification, necrosis | the cell is ageing; the room shrinks |
| 3 | protein aggregates | proteostasis fails; junk accumulates |
| 4 | angiogenesis, feeding nucleus | the cell turns cancerous |

That is the hallmarks-of-ageing progression running into the hallmarks of cancer.
After a cell turns cancerous, two things happen in real biology, in this order:
**the body notices**, and **the cell tries to leave**.

## Recommended: Gen 5 is the immune response

The body notices. Immune cells arrive from outside the membrane and start
clearing the abnormal cell.

Why this one:

- **It is the honest next beat.** Every other candidate is a variation on
  pressure the player already has; this is the first time the world outside the
  cell has ever acted, which is a genuinely new idea after twelve minutes of play.
- **It reuses T57.** T57 builds the game's first entity that chases the player.
  Immune cells are that machinery with different targeting — most of the cost is
  already paid, which matters for a feature this deep into a run.
- **It introduces the first non-hostile faction**, and that is the new verb.
  Immune cells hunt the **nucleus and its hunters too**, not only the player. So
  the player can *bait* — lead an immune cell into the thing that is chasing
  them and let the two fight. Three-way pressure out of one entity type, no new
  systems.
- It fits the fiction exactly: the player is a microtubule inside a cell that has
  become a threat to the organism. The immune system is not wrong to be there.
  That ambiguity is interesting and it costs nothing to implement.

Design constraints when it is written:

- Immune cells enter **through the membrane**, from outside — the one direction
  nothing has ever come from. Telegraph the entry.
- They must be in `spatialGrid`, `checkCollision` **and** `raycast` (§4.1).
- Their fight with the nucleus's hunters must be visible, or the bait mechanic is
  invisible and players will never discover it.
- They should not be dodgeable forever *or* unavoidable. The generation ends.

## Then: Gen 6 is metastasis — and it is the game's first win condition

The cell tries to leave. The membrane ruptures and the player escapes into the
extracellular matrix.

This is the more valuable of the two, for one reason that has nothing to do with
biology: **this game currently has no way to win.** Every run ends in death. That
is fine for an arcade survival game, but the owner is building scoring, high
scores and upgrades (Track L, T53–T55), and a progression system with no
completed outcome is a strange thing — the best possible run is still "died a bit
later than last time".

An escape gives:

- a real ending, and a reason for a run to have a shape
- the top score band in T53 (reaching Gen 4 should be worth a lot; escaping should
  be worth the most)
- a natural place for T55's upgrades to pay off — you buy tools to reach an
  ending you can actually reach

Mechanically it is the largest thing on this page: the arena stops being one
closed ellipse. Mitosis already moves the player between two cells, so the code
knows how to relocate an arena mid-round — but "the next space is not a cell" is
a genuinely new arena type and should be scoped as its own phase when the time
comes.

## The pacing problem this exposes

At `MITOSIS_INTERVAL = 240`, Gen 4 arrives at roughly **twelve minutes** and Gen 6
at around twenty. Almost nobody will see content placed there. Before building
Gen 5, one of these has to change:

1. **Shorten the interval as generations rise** — later generations arrive faster,
   which also matches the fiction of a cell losing control.
2. **Advance on achievement, not on the clock.** T52 introduces the nucleus feed
   meter; a generation could advance when that meter fills rather than when four
   minutes elapse. This ties progression to *how the round went* instead of how
   long the player waited, and it makes T51's ATP and T52's interception
   genuinely consequential — slowing the nucleus would slow the whole ladder.

**Recommended: (2), with (1) as the fallback.** It costs little, it makes two
already-planned mechanics matter more, and it fixes the deeper problem that
survival time currently rewards turtling.

## Order

Nothing here starts until T52 and T57 have landed and been played. Then, in
order: the pacing change, Gen 5 (immune response), Gen 6 (escape) — with Track L
built in between, since scoring is what gives an escape ending somewhere to land.

---

## Task files — written 2026-08-14

T52 and T57 have now landed **and been played**, and Track L is done, so the
preconditions above are met. Scoped as **Track N** on the board:

| | | |
|---|---|---|
| [T71](tasks/T71-generation-pacing.md) | the pacing change | `READY` — do this first |
| [T72](tasks/T72-gen5-immune-response.md) | Gen 5, immune response and baiting | `BLOCKED` on T71 |
| [T73](tasks/T73-gen6-escape.md) | Gen 6, the escape and the first win condition | `BLOCKED` on T72, resumable |

The recommendations in this document were carried into the task files intact:
option (2) for pacing, baiting as Gen 5's new verb, and the escape as the game's
first win condition rather than one more hazard.
