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

- [ ] Host simulates; clients render only
- [ ] Traces never sent — reconstructed from head positions
- [ ] Events reliable/ordered; snapshots unreliable/unordered, with staleness discard
- [ ] `isGap` carried so remote gaps render
- [ ] Bandwidth measured and reported
- [ ] Deaths agree across all peers over 10 trials
- [ ] Client-side gameplay logic provably not running
- [ ] Input latency measured, as T31's baseline
- [ ] `docs/TASKS.md`: T30 → `DONE`; T31 → `READY`
