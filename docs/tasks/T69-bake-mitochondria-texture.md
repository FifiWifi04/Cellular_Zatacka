# T69 — Extend the bake to mitochondria, without touching the spine

**Track:** M (Phase 2, unparked) · **Depends on:** T68 **+ owner sign-off** · **Risk:** high (this is the case that broke last time) · **Est. diff:** ~100 lines

**BLOCKED until the owner has looked at T68's screenshots and said to continue.**
A routine must not unblock this itself.

---

## Why this one is dangerous

The mitochondrion's hitbox is a **5-segment quadratic spine** derived from
`radius`, `bendY` and `rotation`. The first attempt at Phase 2 "solved" the
mismatch between that curve and a rectangular sprite by setting `bendY = 0` —
straightening the *physics* to match the *art*. That is backwards
(`AGENT_CONDUCT.md` §4.4), and it flattened a deliberate piece of the game's feel.

Baking from `createOrganelleGraphics()` avoids the problem entirely, because that
drawing already follows the spine. The texture curves because the source curves.

**The rule: never change a hitbox to match a sprite.** If they disagree, the
sprite is wrong. If you cannot make them agree, stop and report.

## Design

Same shape as T68 — bake per variant in `generateMap()`, largest drawn size,
behind the same `USE_BAKED_ORGANELLE_TEXTURES` flag — with two additions:

1. **`bendY` varies per organelle**, so a single shared texture cannot serve them
   all. Either bake per distinct `bendY` bucket (quantise, and say how coarsely),
   or bake one straight texture and accept that the *drawn* curve is lost — which
   would be a visible regression and is **not** acceptable. Choose the first, or
   report that the bake does not suit this type and leave mitochondria on the
   vector path. **Leaving one type on the vector path is a perfectly good
   outcome** — the flag already supports a mixed build.
2. **Rotation stays a sprite property**, not baked in. Bake unrotated, set
   `sprite.rotation`, exactly as the hitbox transform already does (§4.3).

## Verification

1. Console clean.
2. Screenshot diff flag on vs off at 0.6 and 2.0 zoom, **including a curved
   (`bendY` far from 0) specimen** — the whole risk is here.
3. **Collision byte-identical.** Head-on into a mitochondrion at Very Fast under
   4× fuzzer dilation, flag on and off, same death time. Then the same against a
   strongly curved one.
4. **`bendY` is never written by this diff** — confirm with `git diff`. If it
   appears, the task has failed.
5. Texture count bounded — state how many variants get baked and why that number
   cannot grow with organelle count.
6. No leak across 3 rounds and a mitosis.
7. Regression sweep §7.6.

## Definition of done

- [ ] Mitochondria baked with their curve intact, **or** explicitly left on the
      vector path with the reason stated
- [ ] `bendY` untouched, proven by diff
- [ ] Collision identical on a curved specimen
- [ ] Texture variant count bounded and justified
- [ ] `docs/TASKS.md`: T69 → `DONE`

---

## Findings

*(Bucketing scheme if used; the curved-specimen screenshots and timings.)*
