# T70 — Finish the set, then find out whether it was worth it

**Track:** M (Phase 2, unparked) · **Depends on:** T69 · **Risk:** low · **Est. diff:** ~90 lines

**BLOCKED until T69 is done.**

---

## Part 1 — the remaining types

Vesicles and virus particles, same pattern as T68: bake from the existing
drawing, per variant, behind `USE_BAKED_ORGANELLE_TEXTURES`, hitboxes untouched.
Both are circles, so neither carries T69's geometry risk.

## Part 2 — the measurement that justifies the whole exercise

This is the actual point of the task. **Does the pipeline make the game faster?**

Measure, flag off vs flag on, same seed, same scene:

- draw calls per frame
- frame time, 4 players at Gen 3 with the arena full
- frame time in split-screen, which renders the world once per viewport and is
  where a draw-call win should show up largest
- memory: total texture bytes added

Report all four. **If the pipeline is not measurably better, say so plainly.**
That is a legitimate and useful result — the flag makes reverting one line, and
the honest answer is worth more than a kept change that bought nothing.

Recommend a default for the flag based on the numbers, and say why.

## Verification

1. Console clean.
2. All four measurements, both flag states, with the scene described precisely
   enough to repeat.
3. Screenshot diffs for the new types at 0.6 and 2.0 zoom.
4. Collision unchanged for vesicles and virus particles.
5. No leak across 3 rounds and a mitosis.
6. Regression sweep §7.6.

## Definition of done

- [ ] Vesicles and virus baked, hitboxes untouched
- [ ] Draw calls, frame time (shared + split), texture memory — all four reported
      for both flag states
- [ ] A recommended default for the flag, with reasoning
- [ ] `docs/TASKS.md`: T70 → `DONE`

---

## Findings

*(The four measurements and the recommendation.)*
