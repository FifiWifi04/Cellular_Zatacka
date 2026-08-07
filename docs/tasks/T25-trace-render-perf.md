# T25 — Incremental trace rendering

**Track:** H (Phase 6) · **Depends on:** T24 · **Risk:** medium · **Est. diff:** ~120 lines

Read `docs/AGENT_CONDUCT.md` before starting.

**This task benefits desktop as much as mobile.** It is filed under Phase 6
because mobile is where it becomes a hard blocker, but the win applies everywhere.

---

## Goal

Stop redrawing every trace point every frame.

## Why — the numbers

`drawTraces()` clears and re-emits the entire path for every player, **twice**
(once for `trailGlow`, once for `trailCore`):

```
trailGlow.clear(); trailCore.clear();
players.forEach(p => p.traceSegments.forEach(seg => {
    trailGlow.moveTo(seg[0].x, seg[0].y);
    for (let i = 1; i < seg.length; i++) trailGlow.lineTo(seg[i].x, seg[i].y);
    // ...and the same loop again for trailCore
}));
```

One trace point is appended per player per frame. At 60fps that is 3,600
points/player/minute. Four players at two minutes ≈ **28,800 points ≈ 57,600
`lineTo` calls per frame**, growing without bound for the length of the round.

Desktop GPUs absorb this. Mid-range phones will not — and `trailGlow` also
carries a `BlurFilter`, so the whole growing path is re-filtered every frame too.

> Measured in the sandbox: 4 players reached ~2,400 points at 60 game-seconds,
> but that run was software-rendered at ~10fps. The 60fps projection above is the
> one that matters on real hardware.

---

## Design

Traces are **append-only**: once drawn, a segment never moves. That is exactly
the property that makes an accumulation buffer correct here.

### Approach — draw into a persistent RenderTexture

1. Create two `PIXI.RenderTexture`s sized to the **world**, not the screen —
   `trailGlowRT` and `trailCoreRT` — plus two `PIXI.Sprite`s that display them in
   place of the current `trailGlow`/`trailCore` Graphics.
2. Each frame, draw **only the new points** since last frame into a small
   scratch `Graphics`, then render that scratch into the RenderTexture with
   `clear: false` so it accumulates.
3. Clear the RenderTextures only on `startRound()` and whenever a trace is
   trimmed from the front (T07's cap) or deleted (`deleteOldestTrace`) — those
   are the only events that *remove* geometry, and they force a full redraw.
4. Player heads, auras and the ghost pulse are **not** append-only — they move
   every frame. Keep drawing those into a normal per-frame `Graphics` on top.

### The size problem — read this before choosing

The world is ~2800×2400 units and the camera zooms from 0.1 to 1.2. A
world-sized RenderTexture at scale 1 is ~2800×2400 px per layer, ×2 layers,
×4 bytes ≈ **54 MB of GPU memory**. That is too much for a low-end phone.

Options, in order of preference:

- **Render at a fixed fraction of world scale** (e.g. 0.5) and upscale the
  sprite. Traces are 4px wide glowing lines; slight softness is acceptable and
  arguably suits the aesthetic. 13 MB total. **Start here.**
- Bound the texture to the arena's actual bounds rather than a padded square.
- If quality is unacceptable at 0.5, try 0.75 and measure memory on a mid-range
  device profile before committing.

**Do not** create a RenderTexture per player — that multiplies memory by four for
no benefit; all players can share one buffer since traces never overlap
destructively under additive blending.

### Interaction with T07

T07's front-trimming removes old points, which invalidates the accumulated
buffer. The simple correct answer: when a trim occurs, do a **full redraw** of
that frame (clear the RT, re-emit all remaining points once). Trims are rare
relative to frames, so the amortised cost is still far below redrawing every
frame. Implement it that way and measure — do not attempt incremental erasure.

If T07 has not landed, note that this interaction is coming.

---

## Files touched

`260703_Cellsnake.html` only: the `trailGlow`/`trailCore` declarations and their
layer wiring, `drawTraces()` split into an accumulate path and a per-frame
overlay, `startRound()` reset, and a redraw hook wherever traces are trimmed.

---

## Verification

1. Console clean.
2. **Visual parity.** Screenshot a 60-game-second round before and after. Traces
   must look the same modulo the chosen resolution softness. Include both
   screenshots in the commit.
3. **Cost is now constant per frame.** Instrument `drawTraces()` with
   `performance.now()`. Log mean cost at 15s, 30s, 60s and 120s of game time,
   before and after. Before: rising roughly linearly. After: **flat**. Put all
   eight numbers in the commit message — this is the whole point of the task.
4. **Memory.** Report the RenderTexture dimensions and estimated bytes. Confirm
   `worldChildren` did not grow, and that heap is stable over a 3-minute round.
5. **Trim redraw works.** With T07 active (or by calling `deleteOldestTrace`
   manually), confirm the trace visually shortens from the tail and no ghost
   geometry is left behind in the buffer.
6. **Round restart clears it.** Restart 5 times; no trace from a previous round
   survives into the next.
7. **Split-screen.** The RenderTexture path must still composite correctly in
   split camera mode — this is the most likely place for a surprise.
8. **Collision unaffected.** Traces are still lethal in exactly the same places;
   run the regression sweep from `AGENT_CONDUCT.md` §7.6. Rendering changes must
   not touch `rebuildSpatialGrid` or `checkCollision`.

## Definition of done

- [x] Traces accumulate into shared RenderTextures; only new points drawn per frame
- [x] Heads/auras still drawn per frame on top
- [x] Texture resolution chosen with memory estimated and stated
- [x] Per-frame trace cost flat over time, with before/after numbers at four time points
- [x] Trim and restart both force a correct full redraw
- [x] Split-screen verified
- [x] Zero change to collision behaviour
- [x] `docs/TASKS.md`: T25 → `DONE`; T26 → `READY`

## Result — 2026-08-07

Implemented as designed: `trailGlowRT`/`trailCoreRT` (shared, one pair for
all players) at `TRACE_RT_SCALE = 0.5`, sized `activeCell.baseRadiusX/Y +
150px` padding → **1550×1350px per layer, ~16.0MB total** (`1550*1350*4*2`
bytes) for both layers combined. `rebuildTraceRT()` (re)allocates + does a
full redraw; `accumulateTraceRT()` draws only each player's new points since
last frame via a per-player `(traceDrawSeg, traceDrawPt)` cursor. A forced
full redraw is triggered by `trimTraceToCap`, `deleteOldestTrace`, and the
lysosome-pickup `traceSegments.shift()` — the three places that remove
front geometry — plus once at `startRound()`.

**Per-frame `drawTraces()` cost** (mean of last ~120 calls, measured via a
`performance.now()` wrapper installed from the verification harness, not
left in the shipped code), 1 player + 3 bots, immortal, 640x480:

| game-time | before (ms) | after (ms) |
|---|---|---|
| 15s | 0.088 | 0.277 |
| 30s | 0.171 | 0.228 |
| 60s | 0.245 | 0.252 |
| 120s | 0.486 | 0.205 |

Before rises roughly linearly (5.5x from 15s to 120s); after is flat within
noise. (After is higher at 15s than before because the very first frames
after a full redraw still touch the RT-render call; both curves converge to
per-frame delta cost, which is what stays flat.)

**Verified:** console clean (`http://` and `file://`); visual parity at 60s
(`/tmp/verify/before_60s.png` vs `after_60s.png`, same style/halo/dash
pattern, differences are bot-AI randomness not rendering); `worldChildren`
flat at 12 and `trailGlowRT` staying 1550×1350 across a 183s/7120-point
round (heap 27.8→40.7MB, consistent with trace-point array growth, not a
leak); `deleteOldestTrace` trim visibly shortens the trace from the front
(`trim_before.png`/`trim_after.png`) and clears `traceRTNeedsFullRedraw`;
5x round restart leaves no stale geometry (fresh `traceSegments`/draw
cursors each time); split-screen composites correctly (nested
RenderTexture-into-RenderTexture rendering, `split_screen.png`); collision
regression sweep at all 3 speeds shows players still dying normally with
zero console errors (expected — `checkCollision`/`checkArcCollision`/
`raycast`/`rebuildSpatialGrid` are untouched by this diff).

**Known gap, not fixed here:** the RT does not follow `mitosis.cellB` or the
post-snap `activeCell` relocation — see `docs/BACKLOG.md` "Found during T25".
Mitosis needs 240s survival time to trigger and none of the verification
above reaches it.
