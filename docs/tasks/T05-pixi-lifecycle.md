# T05 — PixiJS display-object lifecycle fixes

**Track:** A (Phase 1 gate) · **Depends on:** — · **Risk:** medium-high · **Est. diff:** ~60 lines

Read `docs/AGENT_CONDUCT.md` before starting. This task touches teardown code —
the classic place to introduce a use-after-destroy crash. Be conservative.

---

## Goal

Ensure every PixiJS display object created per round is fully released when the
round restarts, so `startRound()` can be called thousands of times without
growing memory or the display-object count.

## Why

`removeChildren()` detaches children from a container but **does not free them**.
The `Graphics` geometry, the WebGL buffers behind it, and any `RenderTexture`
stay alive as long as anything references them. In this codebase:

- `generateMap()` calls `backgroundLayer.removeChildren()` and
  `rotatingContainer.removeChildren()` with no destroy.
- The organelle reset calls `organellesLayer.removeChildren()` then `.clear()`.
- `drawMitosisVisuals()` rebuilds the organelle layer the same way.
- `splitSprites` / `splitTextures` hold `RenderTexture`s that are only ever
  hidden (`.visible = false`), never resized down or destroyed.

`generateMap()` builds a lot per round: the cell background `Graphics`, up to
~300 membrane-protrusion attempts producing many `Graphics`, a cytosol container
with up to hundreds of blob `Graphics`, the nucleus, the ER/Golgi
`Container` + `Graphics` from `drawArcs()`, and 25 organelle `Graphics`. A fuzz
loop restarting rounds every few seconds will accumulate all of it.

This is the "mathematically stable" evidence the Phase 1 gate asks for, and T06a
cannot produce a meaningful report until this is fixed.

---

## Prerequisites

Read in full: `generateMap()`, `drawArcs()`, `startRound()`, the organelle rebuild
inside `drawMitosisVisuals()`, and the split-screen block in `updateCamera()`.

Note the existing correct patterns to copy:
- `if (window.nucleusMask) { world.removeChild(...); window.nucleusMask.destroy(); }`
  in `generateMap()`
- `organellesLayer.removeChild(org.sprite); org.sprite.destroy();` in the arc
  shatter path

---

## Implementation plan

### Step 1 — One shared teardown helper

Add a single helper near the layer declarations and use it everywhere:

```
// Detach and fully release every child of a container.
function purgeContainer(container) {
    for (let i = container.children.length - 1; i >= 0; i--) {
        let child = container.children[i];
        container.removeChild(child);
        if (child && !child.destroyed) {
            child.destroy({ children: true, texture: false, baseTexture: false });
        }
    }
}
```

`texture: false` is deliberate — nothing here owns a texture except the
split-screen `RenderTexture`s, which are handled separately in Step 4. Destroying
a shared texture by accident is exactly the kind of bug that only shows up three
rounds later.

### Step 2 — Replace the unsafe teardowns

| Location | Change |
|---|---|
| `generateMap()` | `backgroundLayer.removeChildren()` → `purgeContainer(backgroundLayer)` |
| `generateMap()` | `rotatingContainer.removeChildren()` → `purgeContainer(rotatingContainer)` |
| `generateMap()` organelle block | `organellesLayer.removeChildren()` → `purgeContainer(organellesLayer)` (keep the following `.clear()`) |
| `drawMitosisVisuals()` organelle rebuild | same substitution — **but read it carefully first**, see Step 3 |

### Step 3 — The organelle-sprite trap

`drawMitosisVisuals()` contains:

```
organellesLayer.removeChildren();
organellesLayer.clear();
organelles.forEach(o => organellesLayer.addChild(o.sprite));
```

This detaches sprites and **re-adds the same objects**. If you purge (destroy)
here, you destroy sprites that `organelles[]` still references, and the next frame
will re-add destroyed objects — a crash or silent render failure.

**Do not use `purgeContainer` at this site.** Leave `removeChildren()` as-is here,
and add a comment saying why. This site is a re-parent, not a teardown.

The rule to apply generally: purge only where the underlying physics objects are
also being discarded. In `generateMap()`'s organelle block, `organelles = []`
follows, so purging is correct there.

> Confirm this by checking whether `generateMap(keepOrganelles = true)` is ever
> called. If it is, the purge must stay inside the `if (!keepOrganelles)` branch —
> which is where it already lives. Verify, do not assume.

### Step 4 — Split-screen render textures

In `updateCamera()`, `splitSprites` and `splitTextures` grow to match the alive
player count and are then only hidden. They are also never resized when the
window resizes, and `startRound()` only hides them.

Two changes:

1. In `startRound()`, destroy and empty both arrays before the round begins:
   iterate, `sprite.destroy({texture: false})` then `rt.destroy(true)`, then set
   both arrays to `[]`. The camera block already recreates them on demand.
2. In the window `resize` handler, do the same — the textures are created at the
   old `viewW`/`viewH` and are stale after a resize.

Guard both with a `destroyed` check so a double call is harmless.

### Step 5 — Cytosol and protrusion containers

`generateMap()` assigns `cytosolContainer` and creates a
`membraneProtrusionsContainer`, and pushes into module-level arrays
`cytosolParticles` and `membraneProtrusionsList`. Purging `backgroundLayer` frees
the display objects, but the arrays still hold references to `Graphics` objects
that are now destroyed.

Reset both arrays to `[]` in `generateMap()` at the same point the containers are
rebuilt. Search for every read of `cytosolParticles` and
`membraneProtrusionsList` and confirm none of them can run between the purge and
the refill.

---

## Files touched

`260703_Cellsnake.html` only: new `purgeContainer()`, `generateMap()`,
`startRound()`, the `resize` handler. **Not** `drawMitosisVisuals()`'s re-parent
site (Step 3).

---

## Verification

This task is verified by numbers, not by eye.

1. Console clean.
2. **Baseline first.** Before editing, with T04's `fuzzStats` available (or a
   manual snippet if T04 has not landed), record `worldChildren` and
   `performance.memory.usedJSHeapSize` after 1 round and after 30 rounds of
   rapid `startRound()`. Capture the growth.
3. **After.** Same measurement. `worldChildren` must be **flat** (±small
   variance from the randomized protrusion/cytosol counts — compare medians over
   10 rounds, not single samples). Heap must not grow monotonically.
4. **No use-after-destroy.** Run 30 consecutive restarts and confirm zero
   `Cannot read properties of null` / `destroyed` errors, and that the map still
   renders fully on round 30 (background, membrane, protrusions, cytosol,
   nucleus, ER/Golgi, 25 organelles all present).
5. **Split-screen.** Start a 2-player round in split camera, restart 10 times,
   toggle camera mode between restarts. Both viewports must still render.
6. **Resize.** Start split-screen, resize the window, confirm the viewports
   re-create at the new size and nothing goes black.
7. Record before/after `worldChildren` and heap in the commit message.

## Definition of done

- [ ] `purgeContainer()` added and used at every true teardown site
- [ ] The `drawMitosisVisuals()` re-parent site deliberately left alone, with a comment
- [ ] `splitSprites` / `splitTextures` destroyed on `startRound()` and on resize
- [ ] `cytosolParticles` / `membraneProtrusionsList` reset alongside their containers
- [ ] 30-restart run: no errors, map fully renders, `worldChildren` flat
- [ ] Before/after numbers in the commit message
- [ ] `docs/TASKS.md`: T05 → `DONE`; T06a → `READY` if T04 done

## Rollback

If anything renders blank or throws after a restart, revert immediately — a
half-fixed teardown is worse than a leak. Record the failing site under
`## Blocked`.
