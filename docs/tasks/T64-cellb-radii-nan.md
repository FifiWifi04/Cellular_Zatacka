# T64 — `mitosis.cellB` has no radii, so Cell B's wall NaNs whatever touches it

**Track:** K · **Depends on:** — · **Risk:** low (four-line state fix) · **Est. diff:** ~15 lines

Backlog item from 2026-08-06, raised by the owner 2026-08-14 after T63:
*"Yeah I would like to change that."*

---

## Cause

`mitosis.cellB` is created with position only:

```js
mitosis.cellB = { x: activeCell.x, y: activeCell.y };
```

Three wall-containment paths pick a `nearestCell` that can be Cell B and then
read radii straight off it:

- `updateDriftingOrganelles()` — the push-back onto the wall
- the same function's 1000px runaway reset
- `updateVesicles()` — the bounce

All three do arithmetic like
`nearestCell.x + Math.cos(ang) * (nearestCell.radiusX - r - 2)`. With
`radiusX === undefined` that is `NaN`, and it is written straight back to `.x`
and `.y`.

**The consequence is worse than the backlog entry recorded.** It was filed as "no
bounce". It is not — the entity's position becomes **permanently `NaN`** and it
stays in its array, so it is drawn nowhere, collides with nothing, and never
recovers. A silent corruption, not a missing behaviour.

Note `isOutsideCell()` is *not* affected: it reads `activeCell.radiusX` for both
cells, deliberately, and stays as it is.

## Fix

Give Cell B the radii, at creation and in the initialiser:

```js
mitosis.cellB = {
    x: activeCell.x, y: activeCell.y,
    radiusX: activeCell.radiusX, radiusY: activeCell.radiusY
};
```

They are a copy of `activeCell`'s current size, which is safe because
`updateCalcification()` is gated on `mitosis.state === 'idle'` — neither cell can
resize while the event runs. That is the same assumption `isOutsideCell()` and
(before T63) the `cellBBg` bake already relied on, now made explicit.

## Verification

**A/B in a single run**, same vesicle, same start position just outside Cell B's
wall on the far side from Cell A, driven for 3 seconds each way:

| | radii deleted (the old state) | radii present |
|---|---|---|
| position after | **`NaN, NaN`** | `1500, 5958` |
| finite | **false** | true |
| distance from Cell B centre | — | 1058px, inside the 1200px minor radius |
| still in `vesicles[]` | yes (corrupt, forever) | yes |

**Whole-scene NaN sweep**, Gen 2, four players, across a full mitosis event, with
**5 organelles and 4 vesicles deliberately shoved outside Cell B's wall**:

| | before event | after reveal | after the push | 30s later |
|---|---|---|---|---|
| vesicles NaN | 0 | 0 | 0 | 0 |
| organelles NaN | 0 | 0 | 0 | 0 |
| ATP granules NaN | 0 | 0 | 0 | 0 |
| debris NaN | 0 | 0 | 0 | 0 |
| players NaN | 0 | 0 | 0 | 0 |

`worldChildren` flat at 17 throughout; all four players alive; console and
page-error listeners empty; `node --check` passes.

The organelle path is covered by the same fix — an earlier run that had the radii
deleted for three seconds produced exactly one NaN organelle, which is the
predicted corruption showing up on the second of the three paths.

**Behaviour change, stated plainly:** vesicles and organelles now *bounce off*
Cell B's wall instead of being destroyed by it. That is the point of the fix, and
it is a gameplay change — it was held back from T63 for exactly that reason and
done here on the owner's explicit go-ahead.

## Definition of done

- [x] `radiusX`/`radiusY` set at creation and in the initialiser
- [x] A/B evidence that the old state NaNs and the new one does not
- [x] Whole-scene NaN sweep clean under deliberate wall contact
- [x] `worldChildren` flat, console clean
- [x] `docs/TASKS.md`: T64 → `DONE`
