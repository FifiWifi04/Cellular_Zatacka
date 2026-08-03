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

- [ ] Staged `lagging` / `dropped` / `gone` classification with a heartbeat
- [ ] Client-drop behaviour chosen, implemented, and documented
- [ ] Host-drop ends the match visibly with scores, never a freeze
- [ ] Rejoin restores the slot with downsampled trace history, size reported
- [ ] `visibilitychange` handled on both ends, touch inputs released
- [ ] Host-migration limitation stated in the lobby UI and logged in the backlog
- [ ] Every failure mode shows the player something
- [ ] `docs/TASKS.md`: T32 → `DONE` — Phase 7 complete
