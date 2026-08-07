# Coding Agent — Recipe of Conduct

**Read this file completely before touching any code. Every task session starts here.**

This project is a single 3,000-line HTML file with no build step, no test suite,
and no type checking. Nothing will catch your mistake except a human playing the
game. That is why the rules below are strict.

---

## 0. The one-paragraph summary

Do exactly one task file, end to end. Change as few lines as possible. Never
reformat. Every new hazard must be added to **both** the collision path and the
bot's sensor path. Never use point-in-time collision — always swept. Verify in a
real browser before committing. If you find an unrelated bug, write it in
`docs/BACKLOG.md` and leave it alone.

---

## 1. Scope discipline

1. **One task per session.** Open `docs/TASKS.md`, take the lowest-numbered task
   whose status is `READY`, and do only that. Do not start the next one, even if
   it looks trivial and related.
   *Exception:* a task carrying a `## Progress` checklist (marked ⏳ on the board)
   is **resumable** — it spans several sessions, commits per stage, and stays
   `READY` until every stage is ticked. Follow its own "How to run this task
   across sessions" section instead of §9's one-commit rule.
2. **Do not fix what you were not asked to fix.** This codebase has known
   oddities (dead code branches, inconsistent constants, unused variables). If you
   spot one, append it to `docs/BACKLOG.md` with a one-line description and the
   function name. Then continue with your task.
3. **Do not refactor for taste.** No renaming, no extracting helpers "while I'm
   here", no converting `let` to `const`, no reordering functions. A 40-line diff
   that a human can read in one sitting is the goal.
4. **Never reformat or re-indent.** The file mixes styles. Match the style of the
   ten lines surrounding your edit and nothing more. A whitespace-only change
   anywhere in the diff means the task is done wrong.
5. **If the task file is wrong or impossible**, stop, do not improvise a
   different design, and write your finding at the bottom of the task file under a
   `## Blocked` heading. Commit only that.

---

## 2. Where things live (single-file constraint)

- All game code is in `260703_Cellsnake.html`. There is no bundler, no modules,
  no build step.
- **PixiJS 7.3.2 and pixi-filters 5.2.1 are vendored in `vendor/`** and loaded
  with relative `<script src="vendor/...">` tags. They used to come from cdnjs
  and jsdelivr; both hosts are blocked by the egress policy in sandboxed
  sessions, which made the game impossible to run there. **Never point these
  back at a CDN.** If you need to change a version, fetch it from
  `registry.npmjs.org` (allowed) with `npm pack`, and update both files together.
- **The game must keep working when opened directly from `file://`, offline.**
  No `fetch`, no `import`, no XHR, no remote asset loads. This is verified: over
  `file://` the console is completely clean. If a change requires loading
  something over the network, the task is wrong — stop and report.
- Do not create new `.js` or `.css` files for game code, and do not split
  `260703_Cellsnake.html`. `vendor/` (third-party libraries, never edited),
  `tools/` (harness and build scripts) and `dist/` (generated, never hand-edited)
  are exceptions, alongside the PWA files T27 added: `manifest.webmanifest`,
  `sw.js` and `icons/` (192/512/maskable PNGs). A PWA cannot be a single file —
  the manifest and worker must be separate fetchable resources, and both must
  fail harmlessly when fetched from `file://`.
  **If you change `260703_Cellsnake.html`, `vendor/`, the manifest, or the
  icons, bump `CACHE_NAME` in `sw.js`** — without a version bump, players keep
  getting the stale cached game forever after their first visit.

**If you change `260703_Cellsnake.html` or anything in `vendor/`, rebuild the
standalone distributable in the same commit:**

```
python3 tools/build_standalone.py          # rebuild dist/Cellular_Zatacka.html
python3 tools/build_standalone.py --check  # exits 1 if dist/ is stale
```

`dist/Cellular_Zatacka.html` inlines both libraries into one file, so a person
can download that single file and play — no folder, no network. The source HTML
alone does **not** work standalone: it loads `vendor/*.js` by relative path, so
on its own it renders the menu and then dies with `PIXI is not defined`, with
Start doing nothing because the script threw before `window.startRound` was
assigned. A stale `dist/` silently ships an old game, which is worse than none —
`--check` is in the definition of done for that reason.
- Anything you add goes next to the code it belongs with, in the existing
  `// --- N. Section ---` structure.

---

## 3. Anchoring your edits

**Line numbers in task files are approximate and drift as tasks land.** Never
trust them.

- Locate code by **function name** (`function raycast(`) or by a **unique search
  string** quoted in the task file.
- Before editing, read the whole function you are about to change, not just the
  lines you plan to touch.
- If a search string in the task file does not match, a previous task changed it.
  Search for the function name instead, read it, and adapt. Note the drift in your
  commit message.

---

## 4. The five traps in this codebase

These are the mistakes that have actually happened here. Read them every time.

### 4.1 Hazards must be added in TWO places

There are two independent consumers of world geometry:

| Consumer | Function | Purpose |
|---|---|---|
| Physics | `checkCollision()` (+ `checkArcCollision()`, and the inline microtubule/virus loops in `gameLoop`) | Kills the player |
| Sensor | `raycast()` | Lets the bot see |

**Every lethal thing must appear in both.** The current bot is blind to
microtubules and to the ER/Golgi walls precisely because someone added them to
the physics path only. If your task adds or changes a hazard, it is not done
until both paths agree. State in your commit message that you updated both.

### 4.2 Collision must be swept, never point-in-time

Players move up to `3.5 * delta` pixels per frame and hitboxes are ~2.4px
(`TRACE_HITBOX = TRACE_WIDTH * 0.6`). A point-in-time test tunnels straight
through walls.

- Use the existing helpers: `segSegDistSq(ax,ay,bx,by, cx,cy,dx,dy)` for
  segment-vs-segment, `ptSegDistSq(px,py, x1,y1,x2,y2)` for point-vs-segment.
- The player's step is the segment from `(player.x, player.y)` to the candidate
  `(nextX, nextY)`. Test that segment, not the endpoint.
- The one existing point-in-time test (the microtubule AABB check in `gameLoop`)
  is a known defect; it is fixed by task T02. Do not copy its pattern.

### 4.3 Three coordinate frames — know which one you are in

| Data | Frame |
|---|---|
| `players[].x/y`, `organelles[].x/y`, `vesicles[]`, `infection.particles[]`, `mitosis.microtubules[]`, `activeCell`, `mitosis.cellB` | **World** — absolute pixels |
| `centralHitboxes[].points[]` (ER + Golgi) | **Cell-local, un-rotated** — relative to `activeCell.x/y`, before `globalRotation` is applied |
| Mitochondrion spine points | **Organelle-local** — relative to `org.x/y`, before `org.rotation` |

`rotatingContainer` is rendered with `rotation = globalRotation`, which is why
`checkArcCollision()` un-rotates the player position by `-globalRotation` before
comparing against `centralHitboxes`. If you compare a world coordinate directly
against a cell-local hitbox, the collision will be silently wrong by up to the
full rotation angle and will *look* fine for the first few seconds of a round.

### 4.4a New systems: keep update and draw in separate functions

Simulation and rendering are currently fused — `updateVesicles()` calls
`dynamicLayer.clear()` and draws while it simulates. T22 untangles this, and
Phase 7 (multiplayer) cannot happen until it does.

**Do not add to the debt.** Any new system you write must be two functions:

```
function updateThing(dt) { /* state only — no PIXI, no layers, no sprites */ }
function drawThing()     { /* reads state, draws — never mutates state */ }
```

This costs nothing to do up front and is expensive to retrofit. It applies to
every Phase 3 mechanic (the malignant mass, necrosis, calcification, the gravity
well) and to Phase 4's particles.

### 4.4 Physics state is authoritative; visuals only mirror it

This rule exists because a mitochondrion's drawn shape once drifted out of sync
with its hitbox and players died to invisible walls.

- The plain-object fields (`o.x`, `o.y`, `o.rotation`, `o.bendY`, `o.radius`) are
  the truth.
- The display object (`o.sprite`) is written **from** those fields, every frame,
  and never written back. See the tail of `updateDriftingOrganelles()` for the
  correct pattern.
- Never derive a hitbox from a display object's `.x`, `.width`, `.getBounds()`,
  or transform. Never let a draw routine mutate physics state.
- If you add a new hazard, give it plain-object physics fields first, then draw
  from them.

### 4.5 The camera owns `world.x/y/scale`

`updateCamera()` writes `world.x`, `world.y`, `world.scale` every frame with
lerps. Anything else that writes those values (screenshake is the obvious one)
must apply as an **offset after** `updateCamera()` has run, and must be removed
or recomputed from a stored base each frame. Adding to `world.x` without
subtracting it again accumulates and drifts the camera off the map within
seconds.

---

## 5. Performance rules

`gameLoop` runs at 60fps and calls `rebuildSpatialGrid()` once, then
`checkCollision()` once per player and `raycast()` three times per bot.

- **No allocation in the per-step hot path.** No `new Set()`, no `[]`, no
  `.map()`, no object literals inside a loop that runs per ray-step or per grid
  cell. Hoist buffers outside the function and reuse them, or use an integer
  stamp array for de-duplication.
- Reuse the module-level scratch arrays that tasks introduce; do not reallocate.
- `players.find()` inside a per-item loop is a linear scan — hoist it.
- If a task asks you to make something faster, measure before and after with
  `performance.now()` around the call, print to console, and put the two numbers
  in the commit message. "Should be faster" is not evidence.

---

## 6. Dev mode is currently overloaded — do not assume

`devMode` (toggled by `` ` ``/`~`/`½`) currently does **two unrelated things**:
it disables every death check (`!devMode` guards in `gameLoop`), and it gates the
fuzzer (`keys['f']`). This means the fuzzer presently cannot detect collision
bugs at all.

Task **T04** separates these flags. Until T04 has landed:
- Do not add new `!devMode` guards.
- Do not rely on the fuzzer to validate collision behaviour.
After T04, follow the flags defined there.

---

## 7. Verification — mandatory before every commit

A task is not done because the code looks right. Run all of these:

1. **Syntax check.** The file must parse. Extract the script and check it, e.g.
   `node --check` on the extracted `<script>` body, or simply load the page and
   confirm no `SyntaxError`.
2. **Load check.** Serve the folder (`python3 -m http.server 8083`) and open
   `260703_Cellsnake.html`. The browser console must be **completely clean** — no
   errors, no warnings you introduced.
3. **Play check.** Start a round with 1 player + 1 AI bot. Play for at least 30
   seconds. Confirm: the bot moves and does not immediately die; traces draw;
   vesicles spawn and can be collected; nothing flickers or teleports.
4. **Headless check.** `run_test.py` drives headless Chrome and captures frames.
   Its hard-coded Windows paths must be updated to relative paths before use (see
   `docs/BACKLOG.md`). Use it for anything touching mitosis, and attach the frame
   observations to your commit message.
5. **Task-specific checks.** Each task file has a `## Verification` section.
   Every item in it must pass.
6. **Regression sweep for collision work.** If you touched `checkCollision`,
   `checkArcCollision`, `raycast`, or `rebuildSpatialGrid`: play one round in each
   of the three speed settings and confirm you can still die by (a) the outer
   membrane, (b) your own trace, (c) an organelle, and that you can still survive
   a near-miss along your own neck.

**If the console shows an error, do not commit.**

---

## 8. Definition of done

- [ ] Exactly one task implemented, nothing else
- [ ] All items in that task's `## Verification` section pass
- [ ] Browser console clean
- [ ] `python3 tools/build_standalone.py --check` passes (rebuild if you touched
      the game file or `vendor/`)
- [ ] Diff contains no reformatting, no renames, no unrelated changes
- [ ] Both the physics path and the sensor path updated, if a hazard changed
- [ ] Any incidental findings written to `docs/BACKLOG.md`
- [ ] Task status in `docs/TASKS.md` changed from `READY` to `DONE`
- [ ] Committed and pushed to the working branch

---

## 9. Git

- Work on the branch named in the session instructions. Do not push to `main`.
- One commit per task. If you need a fixup, amend rather than stacking noise.
- Commit message format:

```
T07: bound per-player trace growth with front-trimming

<2-4 lines: what changed, which functions, what was measured/verified>

Verified: console clean; 60s round at Very Fast; membrane/self/organelle
deaths still trigger; trace point count capped at 4000 (was ~7200 @ 2min).
```

- Push with `git push -u origin <branch>`. On network failure retry up to 4
  times with 2s/4s/8s/16s backoff.
- Do **not** open a pull request unless explicitly asked.

---

## 10. When you are unsure

Ranked, best first:

1. Re-read the relevant function in full — the answer is usually there.
2. Re-read the trap in section 4 that applies.
3. Implement the **smaller, more conservative** option and note the alternative
   in `docs/BACKLOG.md`.
4. If neither option is safe, stop and write `## Blocked` in the task file.

Never guess at physics constants. Never "improve" a formula you were not asked to
change. Never delete code you do not understand — if it looks dead, say so in the
backlog and leave it.
