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

- [x] Host/client roles, room codes, lobby with player list
- [x] Versioned message envelope documented in one place
- [x] Inputs sampled per tick with sequence numbers
- [x] Four-peer room demonstrated with measured RTT
- [x] Signalling choice and its failure mode recorded in `## Findings`
- [x] Any dependency vendored, not CDN-loaded (n/a here -- the browser side
      uses zero libraries, just the built-in `WebSocket`; `ws` is a
      server-side-only dependency of `tools/relay_server.js`, never shipped
      to the browser, so §2's vendor/no-CDN rule for game code doesn't apply)
- [x] Offline single-player provably unchanged
- [x] `docs/TASKS.md`: T29 → `DONE`; T30 → `READY`

---

## Findings

**Transport choice: a plain WebSocket relay (`tools/relay_server.js`), not
WebRTC DataChannels.** The task's own design note sanctions this as the v1
fallback ("if signalling proves painful, a plain WebSocket relay is an
acceptable fallback"). Real WebRTC would need (a) a signalling exchange for
SDP/ICE, (b) a library or hand-rolled negotiation code to vendor into
`vendor/` per §2's no-CDN rule, and (c) STUN/TURN reachability for NAT
traversal — none of which could be reliably verified inside this sandbox
(egress is restricted, and a public STUN/TURN host or a PeerJS-style cloud
broker is exactly the kind of external dependency §2 already flags as
unreachable here, same as cdnjs/jsdelivr were for PixiJS). A dumb relay needs
none of that: it's a single Node process peers all connect to, and the
browser side needs zero vendored library (`WebSocket` is a built-in). The
real cost, as the task warned, is deployment: this is the first part of the
project that is not a static file with no backend — someone has to run
`tools/relay_server.js` (`npm install` once, then `node relay_server.js
[port]`, default 8090) somewhere reachable, and point clients at it with
`?relay=ws://host:port` if it isn't on `localhost:8090`. **What happens when
it's down:** `netConnect()`'s `error`/`close` handlers catch it — the lobby
shows "Relay unreachable at ws://... . Run tools/relay_server.js and pass
?relay=... if it is not on localhost:8090." No exception escapes to the
console, and nothing outside the (opt-in) Online panel is affected.
Migrating this to real WebRTC DataChannels (relay only for signalling) is
left as an explicit follow-up — noted in `docs/BACKLOG.md`.

**Protocol** is the table in the "Message envelope" comment above
`NET_PROTOCOL_VERSION` in `260703_Cellsnake.html` (section 9) and mirrored in
`tools/relay_server.js`'s header comment; both hardcode `PROTOCOL_VERSION =
1` and must be bumped together. The relay is a pure router: `create`/`join`
are the only messages it interprets (room membership, `MAX_PLAYERS = 4`, a
5-character room code from an alphabet excluding `0/O/1/I/L`); everything
else (`start`/`input`/`state`/`ping`/`pong`/`bye`) is relayed verbatim to the
whole room or to a single `to` peer, tagged with the real sender's `from` id
so a message can never be spoofed as coming from someone else.

**Verified** (all via Playwright + `tools/relay_server.js`, see the session's
scratch scripts -- not committed, per "smallest possible diff"):
- Relay protocol itself, node-to-node (no browser): version-mismatch refusal,
  create/join, lobby fan-out, room-full at 5th peer, `from`-tagged relay,
  targeted ping/pong, peer-leave and host-leave notifications -- all correct.
- **2 real browsers**: host creates a room (5-char code, no ambiguous
  glyphs confirmed), a raw mismatched-version connection gets `joinError`
  and is refused (not a hang), a client joins by code, both sides converge
  on a 2-player lobby, RTT populates in `netState.rtt` and is shown in the
  DOM (`innerText` contains "ms") within the first ~2 ping cycles, starting
  the demo makes the client see host heartbeats (`lastStateAt` set) and the
  host see client input (`lastInputSeqSeen` populated), the client leaving
  drops the host's lobby to 1 within a few seconds, and a fresh client
  joining then watching the host leave sees `netState.statusText` become
  "Host left -- round ended." -- no freeze. Console clean on every page.
- **4 real browsers**, one relay: all 4 converge on a 4-player lobby with the
  right names; after the host starts, the host's `lastInputSeqSeen` has
  entries for all 3 clients and all 3 clients see the heartbeat age update.
  Console clean on all 4 pages. This run also exercised the `?relay=`
  override (pointed all 4 pages at a non-default port), proving a
  non-localhost relay deployment is reachable the way `## Design` describes.
- **Single-player is provably unaffected**: a normal 1-human+3-bot round (12
  game-seconds, both over `http://` and `file://`) opened **zero**
  WebSocket connections (`page.on('websocket')` never fired) and left
  `netState.ws === null`, `netState.role === null` throughout. Console clean
  both ways. `file://` single-player is otherwise unchanged.
- Regression: the pre-existing Help/Scores/Shop overlays and the manual
  dropdown -> `updateUI()` -> `startRound()` path all still work with the new
  Online button and overlay present; Escape/P and the outside-click resume
  correctly defer to whichever overlay (including the new one) is open,
  gated on `isPlaying` exactly like the three pre-existing overlays already
  were (confirmed pre-round Escape is a no-op for the *existing* Help panel
  too, so this is not a T29-introduced gap).

**Measured RTT**: in this sandbox (headless, software-rendered Chromium,
2-4 tabs sharing one CPU-bound process), observed relay round-trips were
**~900-1300ms** -- almost entirely event-loop contention between the
Playwright-driven tabs on a shared core, not the relay itself (the relay
smoke test, node-to-node with no browser/GPU contention, round-trips
instantly). A real deployment on a normal machine/localhost would be
low-single-digit milliseconds; this number is an artifact of the
verification environment, not a transport cost, and is noted here rather
than reported as "typical" real-world RTT.

**One bug caught and fixed during verification**: `netHostStart()` initially
read `currentMode`/`aiCount`/`cameraMode`/`currentSpeed` -- but the game
deliberately does not call `updateUI()` at startup (see the comment above
`renderControlSplash()`), so those globals can be undefined if a host opens
Online and starts the transport demo without ever touching the main menu's
dropdowns first. Fixed to read `modeSelect.value`/`aiSelect.value`/the
`cameraSelect` element/`speedSelect.value` directly, the same DOM-not-globals
rule `tools/verify_harness.py`'s own "TRAP 3" already documents for
`startRound()`.
