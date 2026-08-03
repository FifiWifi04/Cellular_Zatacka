# T29 — Network transport and lobby

**Track:** I (Phase 7) · **Depends on:** T28 · **Risk:** medium · **Est. diff:** ~250 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Let players in different browsers join a shared room and exchange messages.
**No gameplay yet** — this task delivers connectivity, a lobby, and a message
channel that T30 will carry game state over.

## Why separate from T30

Networking fails in confusing ways (NAT, signalling, ordering, disconnects).
Getting a room of four browsers reliably exchanging heartbeat messages is a
complete piece of work on its own, and debugging it while also debugging state
synchronisation is how netcode projects stall.

---

## Architecture decision — read this before designing

### Host-authoritative, not lockstep

Lockstep (every client simulates from shared inputs) is tempting because it
sends almost nothing. **Do not use it here.** Three reasons, in increasing order
of severity:

1. 95 `Math.random()` call sites, 44 of them inside per-frame update functions.
   All would need a seeded PRNG consumed in identical order everywhere.
2. Any divergence in call order desyncs silently and unrecoverably.
3. **Decisive:** `Math.sin`, `Math.cos`, `Math.atan2` and `Math.hypot` are not
   specified to be bit-identical across JavaScript engines. The game uses them
   in the movement hot path. Chrome and Safari can differ in the last bit, and
   lockstep cannot survive that. There is no clean fix short of lookup tables.

So: **one peer simulates; everyone else sends inputs and renders what they are
told.** Determinism stops mattering entirely.

### Why the bandwidth is trivial

This genre has a lovely property: **the trace is emergent.** You never sync trace
geometry — you sync each head's position and angle, and every client appends its
own trace points using the same rule it already uses locally.

Per tick you need roughly, per player: `x, y, angle, flags` ≈ 12 bytes. Four
players at 30Hz ≈ **1.5 KB/s**. Organelles and vesicles at a lower rate add a
few KB/s. This runs comfortably over anything.

### Transport: WebRTC DataChannel, with a signalling fallback

- **WebRTC DataChannel** in unreliable/unordered mode for state, reliable mode
  for lobby and events. Peer-to-peer, so no game server to host or pay for.
- WebRTC still needs a **signalling** path to exchange offers. Options, cheapest
  first: a public PeerJS broker, a tiny serverless function, or a small
  WebSocket relay. Pick one, and **write down in `## Findings` what it costs and
  what happens when it is unavailable.**
- If signalling proves painful, a plain **WebSocket relay** is an acceptable
  fallback for v1 — simpler, at the cost of hosting something.

This is the first part of the project that **cannot be a single static file with
no backend.** Say so explicitly in the commit message; it is a real change to the
project's deployment story.

---

## Design

### Roles

- **Host** — the peer that runs `stepSimulation`. The player who creates the room.
- **Client** — sends inputs, renders received state.

Host migration on disconnect is **out of scope** — T32 handles disconnects
minimally. If the host leaves in v1, the round ends. Say that in the UI.

### Lobby

- Host creates a room and gets a short **room code** (4–6 characters, no
  ambiguous glyphs — no `0/O`, no `1/I/l`). Codes get read aloud.
- Clients join by code. Show a player list with connection state.
- Host picks mode/speed and starts; the existing `startRound()` config
  (`modeSelect`, `aiSelect`, …) is broadcast so everyone starts identically.
- Cap at 4 players — the existing `playerConfigs` array defines exactly four.

### Message envelope

Define the protocol in **one place**, as a small table in a comment, with a
version number in the handshake. Refuse mismatched versions with a clear message
rather than desyncing mysteriously.

```
{ t: 'hello',  v: 1, name }         client -> host
{ t: 'lobby',  players: [...] }     host -> all
{ t: 'start',  config, seed }       host -> all
{ t: 'input',  seq, left, right, toggle }   client -> host   (unreliable ok)
{ t: 'state',  ... }                host -> all             (T30 fills this in)
{ t: 'bye' }                        either
```

Include `seed` in `start` even though host-authoritative does not need
determinism — it lets clients generate identical *cosmetic* randomness (cytosol
blobs, ribosome dots) so the arenas look alike.

### Input capture

Clients must send **input intent**, not positions. Reuse the existing `keys`
object: sample the three control states each tick and send them. Do not send key
events — send the sampled state per tick, with a sequence number so the host can
detect gaps and reordering.

### This task's deliverable

Four browsers in a room, exchanging `input` and a stub `state` heartbeat, with a
visible connection indicator and a measured round-trip time. **No game state
crosses the wire yet.**

---

## Files touched

`260703_Cellsnake.html` (lobby UI, transport, message handling). If a signalling
library is needed it must be **vendored into `vendor/`** like PixiJS — no CDN,
per `AGENT_CONDUCT.md` §2, and the egress policy blocks CDNs anyway.

---

## Verification

1. Console clean on all peers.
2. **Two browsers connect** via room code and exchange heartbeats.
3. **Four browsers** in one room, all listed, all exchanging input messages.
4. **Round-trip time measured** and displayed. Report typical RTT.
5. **Protocol version mismatch** is refused with a clear message, not a hang.
6. **Client leaving** is detected and removed from the lobby within a few seconds.
7. **Host leaving** ends the round cleanly with an explanatory message — no
   silent freeze.
8. **Single-player is completely unaffected.** The entire networking path must be
   inert unless a room is joined. Play an offline round and confirm no network
   code runs — this is the most important regression check in the task.
9. **`file://` still works** for offline single-player.

## Definition of done

- [ ] Host/client roles, room codes, lobby with player list
- [ ] Versioned message envelope documented in one place
- [ ] Inputs sampled per tick with sequence numbers
- [ ] Four-peer room demonstrated with measured RTT
- [ ] Signalling choice and its failure mode recorded in `## Findings`
- [ ] Any dependency vendored, not CDN-loaded
- [ ] Offline single-player provably unchanged
- [ ] `docs/TASKS.md`: T29 → `DONE`; T30 → `READY`

---

## Findings

*(Which signalling approach, what it costs, what happens when it is down, and
measured RTT.)*
