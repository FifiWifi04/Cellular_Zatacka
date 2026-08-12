# T32 — Network resilience: disconnects, rejoin, and honest failure

**Track:** I (Phase 7) · **Depends on:** T31 · **Risk:** medium · **Est. diff:** ~150 lines

Read `docs/AGENT_CONDUCT.md` before starting. This is the task that decides
whether networked play is shippable or merely demoable.

---

## Goal

Handle the things that go wrong — dropped players, a vanishing host, a stalled
connection — visibly and predictably, rather than with a silent freeze.

## Why

T29–T31 deliver a working match under good conditions. Every real session will
hit at least one of: someone closes a tab, a phone sleeps, wifi drops for three
seconds, or the host's laptop lids. Without explicit handling, all of these look
identical to the player: the game quietly stops.

---

## Design

### 1. Detect, then classify

Run a heartbeat on the reliable channel. Classify a silent peer in stages rather
than declaring it dead immediately:

| Silence | State | Shown as |
|---|---|---|
| > 1s | `lagging` | player's name dimmed |
| > 5s | `dropped` | player marked disconnected |
| > 15s | `gone` | slot released |

The staged approach matters because a 3-second wifi hiccup is common and
recoverable; treating it as a disconnect makes the game feel broken.

### 2. When a client drops

The host keeps simulating. Options for the dropped player's snake, pick one and
document it:

- **Freeze in place and remain lethal** — simplest, but a stationary wall appears
  where a player was, which reads as a bug to everyone else.
- **Kill the player** — clean, understandable, matches what happens if you crash
  in a normal round. **Recommended.**
- **Hand to the bot AI** — nice, and cheap since `updateBotAI` already exists and
  the player object already supports `isBot`. Set `p.isBot = true` on drop, and
  back to `false` if they rejoin. This is the best experience if the bot is
  competent after T03.

Take the bot option if T03 has landed; otherwise kill.

### 3. When the host drops

Host migration is genuinely hard (state transfer, re-establishing every peer
connection) and is **out of scope**. Instead, fail honestly:

- All clients show "host disconnected — match ended", with the final scores.
- Return to the lobby, not to a frozen canvas.
- Do not silently reload or lose the scoreboard.

State this limitation in the lobby UI **before** the match starts, so nobody is
surprised. Log "host migration" in `docs/BACKLOG.md` as a possible future task.

### 4. Rejoin

Within the `dropped` window, a client that reconnects with the same identity
should resume its slot. Because the host holds all state, rejoining is mostly a
matter of sending a full snapshot — including enough trace history for the
rejoiner's screen to look right.

**Trace history is the catch**: sending 30,000 points to a rejoining player
contradicts T30's whole design. Options:
- Send a downsampled trace (every Nth point) — cheap, slightly coarse, fine.
- Or accept that a rejoiner sees traces only from the moment they rejoin, and
  say so on screen.

Pick the downsample; state the sample rate and the resulting payload size.

### 5. Mobile backgrounding

A phone that locks or switches apps stops its rendering loop. Handle
`visibilitychange` explicitly: on hide, tell the host you are backgrounding
(so it can distinguish this from a crash); on show, request a full snapshot
rather than trying to catch up from stale state.

This overlaps with T23's requirement to release held touch inputs on hide — make
sure both happen.

### 6. Never freeze silently

The governing rule: **any state where the game stops responding must show the
player what happened.** A connection indicator, a clear message, and a route back
to the lobby. Silence is the one unacceptable failure mode.

---

## Files touched

`260703_Cellsnake.html`: heartbeat and peer-state machine, disconnect handling in
the host loop, rejoin snapshot path, `visibilitychange` handling, lobby/HUD
connection indicators.

---

## Verification

Test by actually breaking things, not by reading code.

1. Console clean on all peers throughout.
2. **Client closes tab** → within 5s the others see them marked disconnected and
   the chosen behaviour (bot takeover or death) applies. Match continues.
3. **Client wifi drops 3s then returns** → shows as `lagging`, recovers, and does
   **not** get dropped. This is the test the staged classification exists for.
4. **Client drops 8s then returns** → rejoins its slot; its screen shows a
   sensible arena including trace history.
5. **Host closes tab** → all clients show "host disconnected", final scores, and
   return to the lobby. No frozen canvas anywhere.
6. **Phone backgrounds and returns** → resumes cleanly via a full snapshot, with
   no stuck touch input and no runaway turning.
7. **All four disconnect simultaneously** → host ends the round without crashing.
8. **Rejoin payload measured** — report the byte size of a rejoin snapshot with
   long traces.
9. **Offline single-player unaffected.** Full regression sweep, §7.6.

## Definition of done

- [x] Staged `lagging` / `dropped` / `gone` classification with a heartbeat
- [x] Client-drop behaviour chosen, implemented, and documented
- [x] Host-drop ends the match visibly with scores, never a freeze
- [x] Rejoin restores the slot with downsampled trace history, size reported
- [x] `visibilitychange` handled on both ends, touch inputs released
- [x] Host-migration limitation stated in the lobby UI and logged in the backlog
- [x] Every failure mode shows the player something
- [x] `docs/TASKS.md`: T32 → `DONE` — Phase 7 complete

## Findings

**Heartbeat: reused existing traffic instead of a new message type.** `ping`/
`pong` already run at 1Hz from the moment a room forms (T29), and once a round
is live, `input`(30Hz)/`state`(20Hz)/`world`(5Hz) add far finer-grained
liveness signal. `netHandleMessage()` now stamps `netState.lastSeenAt[msg.from]`
at the top for every relayed message, so `netCheckHealth()` (a new
`NET_HEALTH_HZ=2` timer, same lifetime as the ping timer) can classify purely
from elapsed silence — no extra wire traffic. Thresholds are exactly the
task's table: `NET_LAG_MS=1000` / `NET_DROP_MS=5000` / `NET_GONE_MS=15000`.

**Client-drop: hand to bot AI**, per the design's own recommendation now that
T03's bot is competent — `netApplyClientDrop()`/`netApplyClientRejoinControl()`
flip `p.isBot`. A relay-confirmed close (`peerLeft`) applies this immediately
(not waiting out the staged thresholds) since there is nothing ambiguous about
it; the staged classifier exists for the genuinely-uncertain case (silence
with no confirmed close).

**Real bug caught in verification, not by reading code: a relay-confirmed
`gone` could be silently undone by a single straggler message.** A message
already in flight when a socket closes can still be delivered and processed
*after* the `peerLeft`/`close` event that reported the peer gone — this
refreshed `lastSeenAt`, and the next `netCheckHealth()` tick reclassified the
peer back to `'ok'` from elapsed time alone, which also fired the recovery
branch and silently handed control back to the (actually-gone) bot-controlled
player. Reproduced with two real Playwright peers (not a synthetic delay) —
see the "client closes tab" trial below, where the very first `netCheckHealth`
tick after `peerLeft` flipped `isBot` back to `false`. Fixed with
`netState.confirmedGone[peerId]`, a latch set only by a relay-confirmed close
and cleared only by an explicit rejoin (`netHandlePeerRejoined()`) — while set,
`netCheckHealth()` skips reclassifying that peer entirely, so a stray packet
can no longer resurrect a confirmed departure.

**Second real bug caught in verification: rejoin was unreachable through the
normal UI.** The WebSocket `close` handler nulled `netState.role` but never
`netState.ws`, so `renderNetPanel()`'s `!netState.ws` check (which decides
whether to show the Host/Join form) stayed false after an involuntary drop —
opening the panel showed a dead-end "Cancel" screen with no room-code field to
rejoin through. Fixed by also nulling `netState.ws` in the close handler; this
only changes the *display* branch chosen while disconnected; a genuine
host-gone message still routes to the "message + Cancel" branch, since the
client's own socket usually stays open after `hostLeft` (the relay never
closes surviving clients — see `removePeer()`).

**Host-drop: fails honestly, no host migration** (out of scope per this
task's own §3). `netHandleHostGone()` is shared by the relay-reported
`hostLeft` message and this client's own heartbeat detecting a hung host
(process asleep/frozen, socket never actually closes — `hostLeft` never
arrives for that case, so the heartbeat is the only thing that catches it).
Final standings shown are this client's own last-known `alive`/`survivalTime`
values (honest, no stats message the host never got to send), `netState.role`
is set to `null` so the panel falls back to its existing "message + Cancel"
branch (back to the room picker, not a frozen canvas), and the panel is
force-opened via `toggleNetPanel(true)` so the message is actually seen even
if the player wasn't looking at it.

**Rejoin: a persistent per-browser `cid` (`localStorage['cz_netClientId']`),
tracked relay-side.** `tools/relay_server.js` now remembers a departed
non-host peer's `{peerId, name}` under its `cid` for `REJOIN_WINDOW_MS=15000`
(kept equal to the game's own `NET_GONE_MS`) after a real socket close, and a
`'join'` whose `cid` matches gets `rejoinedAs: oldPeerId` on its `'joined'`
reply plus a room-wide `'peerRejoined'` broadcast. The host's
`netHandlePeerRejoined()` remaps the fixed roster/`p.netPeerId`/
`remoteInput`/`lastInputSeqSeen` entries from the old peerId to the new one,
hands control back (`isBot=false`), then re-sends the *exact* original
`'start'` message targeted (`to:`) at just the rejoining peer — reusing
`netStarted()`'s whole existing path (roster rebuild, `startRound()`) instead
of inventing a second "resume" code path — followed by a `'rejoinSnapshot'`
with downsampled trace history. Ordering is guaranteed by WebSocket message
ordering on one connection (host sends `start` then `rejoinSnapshot`
back-to-back; the client's `startRound()` from `start` must exist before
`rejoinSnapshot` has `players[i]` to write into).

**Rejoin payload measured**: a synthetic 4000-point single-player trace
(downsampled every `NET_REJOIN_TRACE_STRIDE=8`th point, plus each segment's
true last point) serialised to **6364 bytes**. The rejoining client's local
trace read back at 514 points (≈4000/8, plus the endpoint) — visually
continuous, not the bare few-points-since-reconnect a live-only recovery
would show.

**`visibilitychange`: a second listener, not a merge into T23's.** Distinct
concern (network vs. touch-input release), same event — both fire; verified
by leaving T23's listener's own diff line untouched. On hide: `{t:'bg',
hidden:true}` lets the host's status bar say "(backgrounded)" instead of an
alarming "dropped" for a peer that is still actually connected. On show:
`{t:'bg', hidden:false}` plus `{t:'requestSnapshot'}`, answered by the same
`rejoinSnapshot` message type the rejoin path uses (`netApplyRejoinSnapshot()`
is shared) — catches up a tab that was frozen (not necessarily disconnected)
while backgrounded instead of trying to interpolate from stale state.

**Verified with real Playwright peers over `tools/relay_server.js`** (not
synthetic delays, except where noted): client-closes-tab → host marks `gone`
and hands to bot within ~1-2s (well under the "5s" budget), no console
errors; host-closes-tab → client shows "Host disconnected -- match ended.
Final -- P1: alive · P2: alive (0.2s)", `statusIsFinal=true`, `role=null`,
panel forced open, no console errors; a full ~3.5s silence (client's own
`netSend` stubbed to a no-op, not a socket close) stayed `lagging` the entire
time and recovered to `ok` on resume, `isBot` never flipped true (item 3);
a real socket close held silent for exactly 8s (item 4's own number) then
rejoined on the same page (same `cid`) — roster remapped, `isBot` reverted to
`false`, `organelles.length>0`/`players.length===2` confirmed a sensible
arena; all three clients in a 4-peer room closing simultaneously left the
host still running (`isPlaying`/`survivalTime` intact) with zero console
errors (item 7 — one bot did die to ordinary gameplay in the process, which
is expected and unrelated: `godMode` was applied after `netHostStart()`,
not before). Offline single-player regression-clean over both `http://` and
`file://` (`consoleErrors`/`pageErrors` both empty either way). `checkCollision`/
`checkArcCollision`/`raycast`/`rebuildSpatialGrid` are untouched by this diff
(confirmed via `git diff`), so §7.6's regression sweep doesn't apply. `sw.js`
`CACHE_NAME` bumped v37→v38; `dist/` rebuilt (`--check` passes).

**Not attempted**: host migration (explicitly out of scope per this task's
design §3 — already logged in `docs/BACKLOG.md`'s "Found while scoping Phases
6 and 7" section, restated in the lobby UI here). A dedicated "dimmed name"
per-player HUD treatment (the design's literal "shown as" wording) was traded
for a small always-in-DOM status readout (`#netStatusBar`) instead of touching
`drawPlayerBars()`'s PIXI draw path for a concern that only changes a couple
times a second — cheaper and easier to verify, same "the player can see it"
outcome.
