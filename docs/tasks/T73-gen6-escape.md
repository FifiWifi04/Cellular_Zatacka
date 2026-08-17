# T73 — Generation 6: the escape, and the game's first win condition

**Track:** N (Phase 9) · **Depends on:** T72 · **Risk:** very high (new arena type) · **Est. diff:** ~400 lines · ⏳ **resumable, one section per session**

Scoped in [`PHASE9-LATE-GAME-ARC.md`](../PHASE9-LATE-GAME-ARC.md). This is the
largest task ever put on this board. **Take one section per session** and commit
each separately, the way T62 was run.

---

## Why this matters more than it looks

**This game has no way to win.** Every run ends in death. That is fine for arcade
survival — but Track L built scoring, persistent high scores and purchasable
upgrades on top of it, and a progression system whose best possible outcome is
"died a bit later than last time" is a strange thing to spend points on.

An escape gives:

- a real ending, and a reason for a run to have a shape
- the top score band in T53 — reaching Gen 4 should be worth a lot; escaping
  should be worth the most in the game
- somewhere for T55's upgrades to pay off *toward*

In fiction: the cell has turned, the immune system has arrived, and the cell's
answer is **metastasis** — it breaks out. The player escapes with it.

---

## Sections

### 1. The rupture — an exit exists

The membrane breaches at a point and stays open. A visible, reachable exit.
Reuse T62 §2/§3's membrane and bridge drawing so it reads as the wall tearing,
not as a hole appearing.

This section alone is playable and testable: the exit exists, it is obvious, and
touching it does nothing yet.

### 2. Leaving the cell

Crossing the rupture takes the player **out**. Mitosis already relocates the
arena mid-round (`activeCell` becomes Cell B), so the machinery for "the arena is
now somewhere else" exists — **read how mitosis does it before inventing
anything**. The difference is that the destination is not a cell.

`isOutsideCell()` currently means "dead". That assumption is threaded through
collision, hazard containment and the camera. Finding every place it is load-
bearing is most of this section's work. **Do not fight it** — if the honest
answer is that the outside needs its own containment rule rather than an
inverted one, say so.

### 3. The extracellular matrix — a different arena

Not a cell: no membrane ring, no nucleus, no ER/Golgi. Fibrous, open, with its
own hazards. Deliberately unlike anything in the game so arriving *feels* like
arrival.

Keep it small. A short corridor that ends is a better first version than an open
world, and it can grow later.

### 4. The win

Reach the far end and the run **ends in victory**. Requirements:

- The end-of-round card (T61) must have a win state, visually distinct from
  elimination.
- T53's score must have a **completion bonus** that makes escaping clearly the
  best outcome — state the weighting and show a worked example against a long
  survival run.
- T54's history must record it, and the high-score table must show that a run was
  completed, not just its number.

### 5. Balance and the bots

Can a bot escape? It should be *possible* but not routine. Report the bot escape
rate over 10 rounds. If bots never reach Gen 6, say so — that is a finding about
the pacing (T71), not necessarily a failure here.

---

## Constraints across every section

- **Nothing before Gen 6 changes.** Every section must leave Gens 1–5 identical;
  prove it per section.
- Any new lethal thing goes in `rebuildSpatialGrid()`, the physics path and
  `raycast()` (§4.1).
- The camera work (T60/T65/T67) is settled — if the escape needs a camera move,
  it goes through the existing settle-then-countdown machinery, not a new one.
- Online (T28–T32): a new arena and a win state are state the host must sync.
  Either handle it or state clearly that Gen 6 is single-player-only for now —
  **that is an acceptable answer**, and it should be a guarded check in the code,
  not just a note.

## Verification (per section)

1. Console clean.
2. Gens 1–5 unaffected — screenshot and a played round each session.
3. Section-specific evidence as described above.
4. `worldChildren` flat; no leak across the transition, which is where leaks in
   this codebase have always been (T05, T33).
5. Regression sweep §7.6.

## Definition of done

- [ ] Sections taken one per session, each committed separately
- [ ] Rupture visible; leaving works; the matrix is a distinct place
- [ ] Win state on the end card, in the score, and in the history
- [ ] Bot escape rate reported
- [ ] Gens 1–5 provably unchanged
- [ ] Online handled or explicitly guarded off
- [ ] `docs/TASKS.md`: T73 → `DONE` when every section is ticked

---

## Progress

- [ ] Section 1 — the rupture
- [ ] Section 2 — leaving the cell
- [ ] Section 3 — the extracellular matrix
- [ ] Section 4 — the win
- [ ] Section 5 — balance and bots

Commit per section (`T73: <section>`). Partial `T73:` commits are expected and do
**not** mean the board is stale. Leave T73 `READY` until every section is ticked.

---

## Findings

*(Per section.)*
