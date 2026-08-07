# T33 — Trace invisible outside Cell A (bridge and Cell B)

**Track:** J (playtest fixes) · **Depends on:** — · **Risk:** medium · **Priority: take first**

Read `docs/AGENT_CONDUCT.md`.

## The bug (owner playtest, 2026-08-07)

> "When crossing the bridge during the mitosis and in the new cell the trace
> disappears, and only reappears when collecting some vesicles."

## Cause — diagnosed, T25 regression

`rebuildTraceRT()` sizes the trace RenderTexture to the **starting cell only**:

```
let halfW = activeCell.baseRadiusX + TRACE_RT_PADDING;   // 1400 + 150
let halfH = activeCell.baseRadiusY + TRACE_RT_PADDING;   // 1200 + 150
traceRTOriginX = activeCell.x - halfW;
```

During mitosis, `mitosis.cellB` sits roughly **3400 px away**. The bridge and all
of Cell B are therefore **entirely outside the texture**, so every trace point
drawn there lands off-buffer and is never displayed.

The "reappears on vesicle pickup" detail fits exactly: a lysosome pickup calls
`traceSegments.shift()`, which forces a **full redraw** — and the full redraw
restores the part of the trace that *is* inside Cell A's bounds. The out-of-bounds
part stays invisible.

**Collision is unaffected** — `rebuildSpatialGrid`/`checkCollision` never read the
RT. So players die to traces they cannot see, which is worse than a cosmetic bug.

## Fix

Size the RT to cover **both cells plus the bridge** whenever mitosis is active.

- Compute bounds from `activeCell` *and* `mitosis.cellB` when
  `mitosis.state !== 'idle'`, plus `TRACE_RT_PADDING`.
- Call `rebuildTraceRT()` when a mitosis event **starts** (bounds change), not
  every frame. It already does a full redraw, so existing trace survives.
- **Watch the memory.** Covering both cells roughly triples the width: at
  `TRACE_RT_SCALE = 0.5` that is ≈3550×1350 → ~19 MB/layer, ~38 MB for the pair.
  Acceptable on desktop, heavy for mobile. If it is too much, either drop the
  scale while mitosis is active or clamp the texture to the union's actual
  bounding box rather than a symmetric expansion. State what you chose and the
  measured bytes.
- Restore the single-cell bounds when the event ends and the round continues.

## Verification

1. Console clean.
2. **The headline test.** Trigger mitosis (dev `Tab` fast-forward), drive across
   the bridge into Cell B, and confirm the trace is drawn continuously the whole
   way — in the bridge and inside Cell B.
3. Drive into your own trace inside Cell B: you die, and the trace you died on
   was visible. Visible geometry and lethal geometry must agree everywhere.
4. Report RT dimensions and bytes before/after, idle and mid-mitosis.
5. `worldChildren` flat and heap stable over a 3-minute round with a mitosis.
6. Split-screen still composites correctly during mitosis.
7. Regression sweep, `AGENT_CONDUCT.md` §7.6.
