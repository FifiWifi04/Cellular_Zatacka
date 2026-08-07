# T37 — Calcification: two membranes visible, organelles bounce oddly

**Track:** J · **Depends on:** — · **Risk:** low-medium

Read `docs/AGENT_CONDUCT.md`.

## The bugs

> "Organelles bounce weirdly when the membrane shrinks, and when the membrane
> shrinks the original membrane stays in place so both of them are visible."

## Cause

**Double membrane.** `generateMap()` bakes the membrane into `cellBg` at the
round's starting radii. T12 added `calcifyLayer`, redrawn each frame at the live
shrinking radii. T12's own task file offered "leave the baked one, it reads as the
old cell wall" as an option and that is what was taken — the owner has now
judged it wrong.

**Fix:** when `genAtLeast(2)` and shrinking has begun, stop drawing the baked
membrane rings so `calcifyLayer` is the only boundary. Either omit those
`lineStyle`/`drawEllipse` calls from `cellBg` when calcification is possible, or
draw the *interior fill* in `cellBg` and let `calcifyLayer` own every ring.
Consider a faint "scar" ring at the original radius **only** if it looks
deliberate — otherwise no second ring at all.

**Organelle bounce.** `updateDriftingOrganelles()` handles the wall with a snap
plus a velocity flip:

```
o.x = nearestCell.x + cos(ang) * (nearestCell.radiusX - o.radius - 2);
o.vx *= -1; o.vy *= -1;
```

With a *moving* wall the organelle gets snapped every frame while the boundary
overtakes it, so it jitters and reverses repeatedly. Fix by reflecting the
velocity about the surface normal **once** and only when it is actually moving
outward — not flipping both components unconditionally — and by giving the snap a
small inward margin so the next frame does not immediately re-trigger it.

## Verification

1. Console clean.
2. **Gen 1 unchanged** — one membrane, organelles behave exactly as before.
3. At Gen 2, only one membrane is visible at all times; screenshot early and late
   in the shrink.
4. Organelles pushed inward by the wall move smoothly — no jitter, no rapid
   reversals. Watch 60 s at Gen 2.
5. No organelle ends up outside the boundary.
6. Death still occurs exactly at the drawn edge, at four compass points, at two
   different shrink stages.
7. Regression sweep §7.6.
