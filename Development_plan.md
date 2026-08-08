# Cellular Zatacka - Master Development Roadmap
Role: Expert PixiJS Game Developer & Architect
Objective: Execute the following 5-Phase production roadmap sequentially. Do not advance to a new phase until the current phase is mathematically stable and performance-tested.

## Critical Constraints & Context
- Engine: HTML5 Canvas via PixiJS (v7+). Local shared-keyboard multiplayer (1-4 players).
- Coding Style: Strict "Greyboxing" isolation. Keep gameplay physics separate from rendering layers.
- Key Objects: `activeCell` (ellipse), `mitosis` (bridge state engine), `players` (array of traces).
- Dev Mode Active: `` ` ``/`~`/`½` toggles dev mode (master switch; `\` also
  works), `,` toggles god mode, `f` toggles the fuzzer, `k` toggles screenshake,
  `n` jumps activeCell.generation +1, `.` toggles the on-screen dev legend,
  `Tab` fast-forwards survivalTime by 15s.

---

## PHASE 1: Automation & Testing Foundation
1.1 Implement a Heuristic AI Bot inside the `players` array.
    - Implement a ray-casting sensor array casting 3 rays (Forward, Left, Right).
    - Detect distances to lethal boundaries (elliptical membrane, player traces, microtubules, virus particles) and rewards (vesicles).
    - Assign weights to each direction and simulate virtual key presses to steer the bot autonomously.
1.2 Implement a "Fuzzer" testing script toggled via Dev Mode.
    - Automatically spawns maximum hazards, triggers rapid state toggles, and restarts rounds instantly to test for memory leaks or `undefined` crashes.

## PHASE 2: Asset Pipeline & Bioluminescent Styling
2.1 Refactor rendering engine to load 2D pre-rendered image files (.png/.webp) instead of drawing vector shapes via `PIXI.Graphics`.
    - Swap primitives for sprites: Organelles, Viruses, Vesicles, and the outer Membrane.
2.2 Apply Additive Blending (`blendMode = PIXI.BLEND_MODES.ADD`) to player head cores, active traces, and vesicle drop zones to establish a glowing, microscopic bioluminescent aesthetic.

## PHASE 3: Content Expansion (Phases 4 & 5)
*Wrap all Phase 3 mechanics in conditional gating: `if (activeCell.generation >= X)`*
3.1 Generation 2 - Membrane Calcification & Organelle Necrosis:
    - Frame-by-frame shrinking of the elliptical membrane radii (`activeCell.radiusX`/`radiusY`).
    - Randomly freeze drifting organelles, turning them stone-gray and switching their collision profile to lethal, static walls.
3.2 Generation 3 - The Malignant Mass:
    - Spawn a static tumor sprite that duplicates/clones an attached block every 10 seconds.
    - If a player hits the mass while their `targetMode === 'attack'`, the block shatters.
3.3 Generation 4 - Angiogenesis:
    - Center a gravity well that exerts a constant, inward pull vector on all spawned vesicles.

## PHASE 4: Visual Polish & "Juice"
> **Mobile budget (added 2026-08-03).** Everything in this phase is full-screen
> GPU work, on top of the `AdvancedBloomFilter` already applied to `world`.
> Phase 6 targets mobile, where full-screen post-processing is the most expensive
> thing a 2D game can do. Build 4.2 and 4.3 so they can be **switched off or
> scaled down** — see `docs/tasks/T26-quality-tier.md`. Designing the off-switch
> in now is far cheaper than retrofitting it.
4.1 Implement a lightweight Camera Screenshake utility. Trigger screen rumble on player elimination, virus explosions, and the Mitosis "Snap".
4.2 Deploy a PixiJS particle emitter splash system for trace locomotion, vesicle collection, and membrane collisions.
4.3 Apply full-screen post-processing filters (e.g., slight chromatic aberration or blur) exclusively during the 1-minute `infection.state === 'warning'` window.

## PHASE 5: User Experience & Deployment
5.1 Re-engineer HTML UI landing menus. Add a prominent "Quick Play" button that skips configurations and launches a 1-player match against an AI Bot instantly.
5.2 Build a clean, scannable control-mapping splash screen displaying input keys for Players 1 through 4.

---

## PHASE 6: Mobile
*Independent of Phases 1-5 — can be built in parallel at any time.*
6.1 Viewport meta, touch steering (screen halves feeding the existing `keys`
    object), gesture suppression, orientation handling.
6.2 Touch-usable menu and HUD, replacing the mouse-hover peek, plus a pause.
6.3 Incremental trace rendering. `drawTraces()` currently re-emits every point of
    every trace twice per frame — ~57,600 `lineTo` calls per frame at 4 players
    after two minutes. This is the mobile blocker, and it helps desktop too.
6.4 Graphics quality tiers with automatic detection and a manual override.
6.5 Installable PWA: manifest, service worker, offline play, home-screen launch.

**Scope:** one player per device. Multi-player on mobile requires Phase 7.

## PHASE 7: Online Multiplayer
*Depends on the simulation/rendering split (`docs/tasks/T22-sim-render-split.md`).*
7.1 Fixed-timestep simulation. Fixes live bugs: gap chance, gap length and
    vesicle spawn are all rolled **per frame**, so a 30fps device gets half the
    gaps, half the vesicles, and gaps half as long in world distance.
7.2 WebRTC transport, room codes, lobby. **Host-authoritative, not lockstep** —
    `Math.sin`/`cos`/`atan2` are not bit-identical across JS engines, so lockstep
    would desync between browsers.
7.3 State synchronisation. Traces are never sent: they are emergent from head
    positions, so bandwidth is ~1.5 KB/s for four players.
7.4 Client-side prediction for your own head; interpolation for everyone else.
    Death, collection and effects are never predicted.
7.5 Disconnect handling, rejoin, and honest failure. No silent freezes.

**Out of scope for v1:** host migration. If the host leaves, the match ends.
