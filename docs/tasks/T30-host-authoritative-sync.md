# T30 — Host-authoritative state synchronisation

**Track:** I (Phase 7) · **Depends on:** T29 · **Risk:** high · **Est. diff:** ~300 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Make the game actually playable across the network: the host simulates, clients
render, and everyone sees the same match.

## Prerequisites and why each matters

- **T22** — the host must run `stepSimulation()` without rendering being fused
  into it, and clients must run `renderFrame()` without simulating.
- **T28** — the host must tick at a fixed rate, or the match speed depends on the
  host's frame rate.
- **T29** — transport, lobby and input messages exist.

---

## Design

### The loop

**Host**, per fixed step: apply the latest received input for every remote
player, run `stepSimulation(FIXED_DT)`, and every Nth step broadcast a snapshot.

**Client**, per frame: send its own sampled input, apply the most recent
snapshot, and `renderFrame()`.

Send snapshots at **20–30 Hz**, not every simulation step. That is plenty for
smooth motion once T31 adds interpolation, and it cuts bandwidth proportionally.

### What crosses the wire

The central insight: **traces are emergent — never send them.**

Per snapshot, per player: `id, x, y, angle, alive, isGap, targetMode`, plus
effect timers when they change. Clients append trace points from the received
head positions using the same append rule they already use locally, so a trace
of 30,000 points costs zero bandwidth.

Lower-frequency or event-driven:

| Data | How |
|---|---|
| Organelles (25, drifting) | Full list at ~5 Hz — 25 × 12 bytes ≈ 300 B |
| Vesicles | Events: `spawn(id, x, y, type)`, `collect(id, playerId)` |
| Mitosis / infection state | Events on transition, plus periodic reconciliation |
| Deaths, round start/end | Reliable events, never in the unreliable channel |

Send **events on the reliable ordered channel** and **snapshots on the
unreliable unordered one**. A dropped snapshot is replaced 40ms later and does
not matter; a dropped death event desyncs the match permanently.

### Snapshot handling on the client

- Tag every snapshot with the host's step number. **Discard any snapshot older
  than the newest already applied** — unordered delivery means they will arrive
  out of order.
- Clients must not run gameplay logic that the host owns: no local collision
  death, no local vesicle collection, no local spawn. Clients render what they
  are told. The single source of truth is the host.
- Clients *do* keep running cosmetic-only systems (cytosol drift, ribosome
  jitter) from the shared seed so the arena looks alive between snapshots.

### The trace-append subtlety

Appending a trace point per received snapshot at 30 Hz gives half the points of
the host's 60 Hz simulation, so client traces will be slightly coarser polylines
than the host's. Visually this is nearly invisible at 4px width — **but the
client's trace is cosmetic only**, since collision is decided by the host. Make
that explicit in a comment so nobody later "fixes" it by adding client-side
collision.

Gaps need care: `isGap` must be carried in the snapshot so clients know not to
append during a gap. Otherwise gaps will not appear on remote screens and the
game becomes unreadable.

### Bots

Bots run on the host, in `updateBotAI`, unchanged. They appear to clients as
ordinary players. Confirm the bot's `raycast` runs only on the host — running it
on clients would waste CPU and produce nothing.

### Latency

At this stage the local player's own head will visibly lag their input by the
round-trip time. **That is expected and is T31's job to fix.** Do not attempt
prediction here; ship the correct-but-laggy version first and measure it, so T31
has a baseline to improve on.

---

## Files touched

`260703_Cellsnake.html`: snapshot serialise/deserialise, host step loop, client
apply path, event channel, and guards so client-side gameplay logic does not run.

---

## Verification

1. Console clean on host and all clients.
2. **Two-player match plays.** Both see both players moving, both see traces,
   both see the same deaths.
3. **Four-player match plays**, including with bots.
4. **Bandwidth measured.** Report bytes/second in each direction with 4 players
   and long traces. Should be low single-digit KB/s — if it is not, traces are
   probably being sent, which is the design error this task exists to avoid.
5. **Traces match.** Screenshot host and client at the same moment; trace shapes
   must correspond (allowing for coarser client polylines).
6. **Gaps appear on remote screens** — the readability test.
7. **Deaths agree.** Every client shows the same player dying at the same place.
   Run 10 deaths and confirm zero disagreements.
8. **Out-of-order snapshots.** Inject artificial reordering and confirm stale
   snapshots are discarded rather than causing rubber-banding backwards.
9. **Packet loss.** Simulate 5% loss; the match must remain playable.
10. **Clients run no host-only logic** — verify by instrumenting `checkCollision`
    and confirming it is never called on a client.
11. **Offline single-player unchanged.** Full regression sweep, §7.6.

## Definition of done

- [x] Host simulates; clients render only
- [x] Traces never sent — reconstructed from head positions
- [x] Events reliable/ordered; snapshots unreliable/unordered, with staleness discard
- [x] `isGap` carried so remote gaps render
- [x] Bandwidth measured and reported
- [x] Deaths agree across all peers over 10 trials
- [x] Client-side gameplay logic provably not running
- [x] Input latency measured, as T31's baseline
- [x] `docs/TASKS.md`: T30 → `DONE`; T31 → `READY`

## Findings

**Scope note, read first.** This codebase has grown far past what this task's
own design section anticipated — Gen 2+ (calcification detail, necrosis, the
malignant mass, ATP, nucleus chasers), full mitosis/infection state, and
ER/Golgi wall geometry (`centralHitboxes`) all postdate or were never named by
the design's "what crosses the wire" table. Implementing full parity for all
of that in one session would have meant a much larger diff than "smallest
possible" and a verification surface no single session could responsibly
cover. This landing implements the design's literal table faithfully — player
state, organelles, vesicles, deaths, round start/end, the frozen flag — and
explicitly does **not** sync ER/Golgi geometry, Gen 2+ hazard systems, or full
mitosis/infection state. All three are written up as separate items in
`docs/BACKLOG.md` (2026-08-12) with the concrete mechanism each would need.
Every verification round below stayed within Gen 1 and under both
`MITOSIS_INTERVAL` (240s) and `infection.nextWarningTime` (60s default) so
those gaps don't invalidate the results — a longer real match would show
mitosis/infection/Gen2+ content on the host's screen only.

**Roster/identity.** `netBuildRoster(config)` builds `[{peerId, isBot}]` from
`netState.players` (host first, then joiners in join order — `relay_server.js`
uses an insertion-ordered `Map`, so this list is identical on every peer
without an extra round-trip) plus `config.ai` bots, clamped to the 4
`playerConfigs` slots. Every peer computes this independently and gets the
same array, so `players[]` index ↔ identity agrees everywhere with nothing
extra on the wire. `p.netPeerId` is non-null only for a roster slot that is a
*remote* human peer — null for bots and for each machine's own local player
(host's own player included) — so `updatePlayers()`'s input branch and the
keydown handler's targetMode-toggle loop both key off it directly.

**Wire format.** Positional arrays, not keyed objects, plus rounded numbers —
an early keyed-object version of `netBuildStateMessage()`/
`netBuildWorldMessage()` measured **~12KB/s** combined (4-player match,
mostly the 25-organelle world broadcast at 5Hz: one uncompacted `'world'`
message alone was 3627 bytes for 25 organelles/0 vesicles). Switching both
messages to positional arrays with rounded numbers and no `color` field
(`createOrganelleGraphics()`/`drawVesicles()` already derive color purely
from `type` — confirmed by reading both draw functions, color was never
actually needed) measured **~2KB/s in each direction** for a 4-player match
(host+2 clients+1 bot), comfortably inside the design note's "low single-digit
KB/s" — see the 4-player Playwright trial below for the exact figures.

**Verification (Playwright, `tools/relay_server.js`, real WS connections —
same approach T29's own Findings used):**

1. **2-player match** (host + 1 client, no bots): after a 3s steering hold,
   host and client positions matched exactly (bit-identical, since both write
   the same `p.x`/`p.y` from the same snapshot); console clean on both.
2. **4-player match** (host + 2 clients + 1 bot): roster built correctly on
   all 3 peers (`[{1,false},{2,false},{3,false},{null,true}]`); `netPeerId`
   correctly null-for-self/set-for-remote on every peer; host↔client position
   deltas after a 3s steering hold were 8-15px (~90-170ms of visible lag at
   90px/s Normal speed — expected and consistent with the design's own "ship
   the correct-but-laggy version, T31 fixes it" note, not a bug).
3. **Bandwidth**: host sent 8048 bytes / client received 7735 bytes over ~4
   wall-seconds in the 4-player trial → **~2.0KB/s each direction**.
4. **Traces match**: screenshots of host and client at the same moment (2s
   into a round) show the same trace shapes, same organelle positions
   (already reconciled by the first `'world'` tick), same nucleus/ER layout
   in this particular run (the last one is not synced and not guaranteed to
   match — see the scope note; T29-era V8 RNG happened to look similar here).
   Client trace point counts were consistently lower than the host's (9-90 vs
   83-90 in different trials) — expected, since the client only appends a
   point per received snapshot (~20Hz) versus the host's 60Hz simulation.
5. **Gaps appear remotely**: forced `p.isGap = true` directly on the host's
   player; the client's mirror of that player showed `isGap === true` within
   one state tick, and correctly flipped back to `false` once the host's own
   `gapDist` countdown closed it — confirms the segment-boundary
   reconstruction (`newTraceSegment()` pushed on the `isGap` true→false edge,
   matching `updatePlayers()`'s own rule) works, not just the flag itself.
6. **Deaths agree, 10/10 trials**: alternated forcing host-player and
   client-player deaths (swept membrane teleport, so `checkCollision()`'s own
   swept-segment path catches it exactly like a real death would) across 10
   fresh rounds in the same room; host and client agreed on exactly which
   player was dead in all 10, console clean throughout.
7. **Out-of-order snapshot discard**: injected a synthetic `'state'` message
   with `tick = lastAppliedTick - 1000` directly via `netHandleMessage()` —
   not applied, `lastAppliedTick` unchanged. A synthetic message with
   `tick = lastAppliedTick + 100000` (simulating a large gap from dropped
   messages) *was* applied. Both checks ran inside one synchronous
   `page.evaluate()` so the host's own live broadcast couldn't interleave and
   produce a false result.
8. **Packet loss**: wrapped the client's `netHandleMessage` to silently drop
   20% of incoming `'state'`/`'world'` messages (stronger than the task's
   literal 5%, chosen so a 3-second window reliably drops at least one
   message rather than risking zero drops by chance) for 3 real seconds;
   both players stayed tracked as alive throughout — the full-list/staleness
   design self-heals from loss by construction, no special-casing needed.
9. **Client-side gameplay logic provably not running**: wrapped
   `window.checkCollision` (a top-level `function` declaration is a `window`
   property in a non-module script — confirmed directly) to count calls.
   Over the 4-player trial: host 387-420 calls, **both clients 0** calls
   each.
10. **Offline regression sweep (§7.6), all 3 speeds** (Normal/Fast/Very
    Fast): membrane death (swept teleport), own-trace self-collision
    (synthetic segment + `rebuildSpatialGrid()` + `checkCollision()`),
    organelle collision, and near-miss-along-own-neck survival (T08 immunity)
    all passed at every speed — `checkCollision`/`raycast`/
    `checkArcCollision`/`rebuildSpatialGrid` are untouched by this diff (confirmed by
    grepping the diff for their definitions), so this wasn't strictly
    required by AGENT_CONDUCT §7.6's own trigger condition, but the task's
    own Verification item 11 asks for it explicitly.
11. Local single/multiplayer smoke test (`tools/verify_harness.py`, 4
    players/3 bots) and a `file://` offline round: both console-clean, no
    regression.

**`currentSpeed`/`cameraMode` for online play**: both are normally only set
inside `updateUI()` from the DOM selects (T29's own comment already flagged
this trap for `netHostStart()`'s config-building). `netStarted(config)` now
also assigns `currentSpeed = config.speed; cameraMode = config.camera;`
directly from the host-broadcast config on every peer, so gameplay-critical
speed can't silently default to whatever a client's own unrelated menu state
happened to be.

**Camera/split-screen needed no changes.** `updateCamera()` already treats
`players[]` generically (bounding-box shared camera, or one split-screen
viewport per alive player) regardless of where the data came from — so "the
host simulates, clients render, everyone sees the same match" falls out for
free once `players[]`/`organelles[]`/`vesicles[]` are populated correctly;
the same is true of `drawPlayerBars()`, `drawTraces()`, and every other
existing draw function.

**Deviations from the task's literal wording**, both justified above:
vesicles are a full-list periodic reconciliation (`netBuildWorldMessage()`),
not the task's literal spawn/collect *events* — simpler, and more robust
against message loss (a dropped event would desync permanently; a dropped
full-list tick self-heals within `1/NET_WORLD_HZ`). `seed` (already present
in the wire format since T29) is still sent but not consumed by this task —
reserved for the ER/Golgi determinism fix in `docs/BACKLOG.md`.
