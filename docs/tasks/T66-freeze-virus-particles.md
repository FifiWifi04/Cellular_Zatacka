# T66 — The virus swarms while the player is frozen

**Track:** J · **Depends on:** T65 · **Risk:** low · **Est. diff:** ~12 lines

Owner report, 2026-08-14: *"the microtubules is still paused when virus particles
are already going around the cell, probably that should be synchronized."*

---

## Cause

`stepSimulation()` gates the world on `isCellFrozen`:

```js
if (!isCellFrozen) {
    updateDriftingOrganelles(...); updateVesicles(...);
    updateNecroticClusters(...); updateNucleusChasers(...); …
}
updateMitosis(deltaSec);
updateInfection(delta, deltaSec);   // <-- outside, deliberately
```

`updateInfection()` sits **outside** that block for a good reason: it owns the
event's state machine — the warning timer, the breach trigger, and T65's
countdown. Freeze that and the event can never end.

But the same function also owns the **particle motion loop**, and that came along
for the ride. So the 30 particles released at the breach spent the entire
countdown swimming around the cell, bouncing off the wall and the organelles,
while every player stood still. The one thing that can kill you during the freeze
was the one thing still moving.

## Fix

Pass `isCellFrozen` in and skip the particle loop when it is set. The state half
still runs every frame. Nothing in the loop is time-critical — it is motion,
wall/organelle bouncing, and lysosome destruction — so it simply stops and
resumes.

Because the flag is `isCellFrozen` rather than an infection-specific one, the
particles now also hold still during a **mitosis** reveal or a **nucleus
transformation** that happens to overlap a live infection, which was the same
inconsistency in two other places.

## Verification

Forced warning, 1 human + 3 bots, sampling per-frame total particle displacement
and tagging each frame by freeze state. Only frames where particles actually
exist (i.e. post-breach) are counted, and the two samples are the same length:

| | frozen (52 frames) | unfrozen (52 frames) |
|---|---|---|
| total particle movement | **0.00** | 24,942.87 |
| max movement in one frame | **0.00** | 543.61 |
| total player movement | 0.00 | 388.50 |

Particles and players are now stopped and moving together, which is the whole
request. 30 particles present at the breach, so the sample is not empty.

T65 unaffected — re-run after this change: breach fires, countdown shows 3/2/1,
zero deaths during the freeze, camera settled at control return, at both frame
rates (`frozenSecondsAfterRelease` 4.34s and 4.42s). Console and page-error
listeners empty; `node --check` passes.

## Definition of done

- [x] Particle loop gated on `isCellFrozen`; state machine still runs
- [x] Zero particle movement while frozen, measured against a live control
- [x] T65's countdown and camera settle unchanged
- [x] `docs/TASKS.md`: T66 → `DONE`
