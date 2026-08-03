# T16 — Camera screenshake utility

**Track:** D (Phase 4 juice) · **Depends on:** T06a · **Risk:** medium (camera) · **Est. diff:** ~60 lines

Read `docs/AGENT_CONDUCT.md` before starting — **especially §4.5**, which exists
because of this exact task.

---

## Goal

A lightweight screenshake utility, triggered on player elimination, virus
explosions, and the mitosis "snap".

Roadmap 4.1:

> Implement a lightweight Camera Screenshake utility. Trigger screen rumble on
> player elimination, virus explosions, and the Mitosis "Snap".

---

## The one way this goes wrong

`updateCamera()` writes `world.x`, `world.y`, and `world.scale` every frame using
**lerps toward a target**:

```
world.x += (targetX - world.x) * 0.05;
```

If screenshake adds an offset to `world.x`, the next frame's lerp treats the
shaken position as the current position and lerps from there. The offset is
partially absorbed into the camera state and never fully removed — the camera
drifts, permanently, a little more with every shake.

**The fix is to keep shake entirely out of `world`'s own transform.** Two safe
options:

### Option A (preferred) — shake a parent container

Create a container that sits between the stage and `world`:

```
stage → shakeRoot → world
```

`updateCamera()` keeps writing `world.x/y/scale` exactly as it does today,
untouched. Screenshake writes only `shakeRoot.x/y`, which nothing else reads or
lerps. Reset `shakeRoot.x = shakeRoot.y = 0` when the shake ends.

This requires one change to the display hierarchy at init — find where
`app.stage.addChild(world)` happens and insert the container. Check whether
anything else references `app.stage.children` or assumes `world` is a direct
child; the split-screen `RenderTexture` code renders `world` explicitly, so
confirm it still works (it should — it renders `world`, not the stage).

### Option B — apply and subtract the same offset

Store `shakeX`/`shakeY`, subtract last frame's offset before `updateCamera()`,
add this frame's after. Correct but fragile — one early `return` in the wrong
place and the offset is never removed.

**Take Option A.** Note in the commit message why.

Also: with split-screen, `world` is rendered into `RenderTexture`s. Decide whether
shake should apply there too (it will not, under Option A, because the textures
render `world` directly). Document the decision; per-viewport shake is a much
bigger job and is out of scope.

---

## Design

### API

```
// magnitude in px, duration in seconds
function addShake(magnitude, duration)
```

Trauma-based, not additive-timer-based, so overlapping triggers combine sanely:

- Keep `shakeTrauma` in 0..1. `addShake` does
  `shakeTrauma = Math.min(1, shakeTrauma + amount)`.
- Decay each frame: `shakeTrauma -= deltaSec / DECAY_TIME`, clamped at 0.
- Offset each frame: `intensity = shakeTrauma²` (squared feels better than
  linear), then
  `shakeRoot.x = (Math.random()*2-1) * MAX_SHAKE_PX * intensity`, same for `y`.
- `const MAX_SHAKE_PX = 24;` at world scale — remember `world.scale` varies from
  0.3 to 1.2, so a fixed pixel offset on `shakeRoot` reads consistently on screen.
  That is another reason Option A is right.

Prefer smoothed noise over pure `Math.random()` if it looks jittery, but start
with random — it is usually fine and it is one line.

### Triggers

Find each site by reading, and add one call:

| Event | Where | Suggested trauma |
|---|---|---|
| Player elimination | every `p.alive = false;` in `gameLoop` | 0.5 |
| Virus explosion | the infection spawn/burst in `updateInfection()` | 0.6 |
| Mitosis "snap" | the snap moment in `updateMitosis()` — search for the comment mentioning the snap | 1.0 |
| Nucleus destruction | where the 15-vesicle burst spawns in `drawMitosisVisuals()` | 0.7 |

There are **several** `p.alive = false` sites (trace/organelle collision,
microtubules, virus contact, sweep ring, hunter chomp). Add the trigger at each,
or better, funnel them through a single `killPlayer(p)` helper — but only if that
refactor stays small. If it touches more than ~15 lines, do the direct calls and
log the refactor in `docs/BACKLOG.md`.

### Accessibility

Add a `let shakeEnabled = true;` flag and a way to turn it off. Screenshake causes
real problems for some players. A checkbox in the menu is ideal; at minimum, a dev
hotkey and `window.shakeEnabled`. Do not ship this without an off switch.

---

## Files touched

`260703_Cellsnake.html` only: display hierarchy at init (`shakeRoot`), shake state
+ `addShake()` + per-frame update in `gameLoop` (after `updateCamera()`), trigger
call sites, an off switch.

---

## Verification

1. Console clean.
2. **No camera drift.** The critical test. Play 5 minutes with frequent deaths and
   at least two mitosis snaps. The camera must track players exactly as it did
   before — no accumulated offset. Compare a screenshot of a known game state
   before and after the task.
3. **Shake fires on all four triggers**, at distinguishable intensities.
4. **Overlapping shakes** (die during a mitosis snap) do not stack into a
   seizure — trauma clamps at 1.
5. **Decays to exactly zero.** After a shake ends, confirm `shakeRoot.x === 0`
   and `shakeRoot.y === 0`, not a residual epsilon.
6. **Split-screen still renders** correctly with shake active.
7. **Off switch works** and fully disables the effect.
8. **Zoom independence.** Trigger a shake during the mitosis reveal (world scale
   ~0.1) and during close play (scale ~1.2). Screen-space magnitude must look
   similar.
9. **No leak.** `worldChildren` flat over 10 minutes.

## Definition of done

- [ ] Option A implemented — `world`'s own transform untouched by shake
- [ ] Trauma-based accumulation with squared falloff
- [ ] All four triggers wired
- [ ] Offset returns to exactly zero
- [ ] Off switch present
- [ ] No camera drift demonstrated over 5 minutes
- [ ] `docs/TASKS.md`: T16 → `DONE`; T17, T18 → `READY`
