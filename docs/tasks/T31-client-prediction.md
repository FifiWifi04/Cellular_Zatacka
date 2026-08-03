# T31 — Client-side prediction and interpolation

**Track:** I (Phase 7) · **Depends on:** T30 · **Risk:** high (feel) · **Est. diff:** ~180 lines

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Make the game *feel* responsive over the network: your own head reacts to your
input immediately, and other players move smoothly rather than snapping between
snapshots.

## Why

After T30 the game is correct but laggy — your head turns one round-trip after
you press the key. At 60ms RTT that is noticeable; at 150ms it is unpleasant.
Zatacka is forgiving compared to a shooter (you hold a turn rather than flicking),
which makes this very achievable.

Two separate problems, two separate solutions:

| Problem | Solution |
|---|---|
| **Your own head lags your input** | Client-side prediction + reconciliation |
| **Other players move in 30 Hz steps** | Interpolation between snapshots |

---

## Part 1 — Interpolate remote players

The easier half. Do it first and ship it before attempting prediction.

Keep a short buffer of the last two or three snapshots per remote player, and
render them **~100ms in the past**, interpolating between the two snapshots that
bracket the render time. Interpolating between known-good states is far more
robust than extrapolating past the newest one.

- Interpolate position linearly and angle via the shortest arc (`atan2` of
  summed unit vectors, or angle-difference wrapping — do not lerp raw radians
  across the ±π boundary).
- Trace points should still be appended from the **snapshot** positions, not the
  interpolated ones, so remote traces stay geometrically faithful.
- The 100ms delay is a deliberate trade: smoother motion, slightly staler
  remote positions. Since the host decides all collisions, staleness is purely
  visual.

## Part 2 — Predict your own head

1. Keep a ring buffer of your recent inputs, each tagged with the sequence
   number T29 already assigns.
2. Apply your input locally the instant you make it, stepping your own head with
   the same movement code the host uses.
3. When a snapshot arrives carrying the host's authoritative position for you,
   **rewind** to that state and **replay** every input newer than the
   acknowledged sequence number.
4. If the replayed result is within a small threshold of your predicted position,
   keep the prediction (avoids visible jitter from tiny discrepancies). If it
   diverges beyond the threshold, snap.

The replay must use the **same movement function** the host uses — factor it out
if necessary so there is literally one implementation. Two copies of movement
code will drift and cause constant mispredictions.

### What must never be predicted

Predict **only your own head position and angle**. Do not predict:

- death (a mispredicted death is far worse than a late one),
- vesicle collection,
- any effect activation.

Those stay host-authoritative and arrive as events. A player seeing themselves
die and then un-die is the worst possible outcome; a 100ms-late death is barely
noticeable.

---

## Files touched

`260703_Cellsnake.html`: input ring buffer, snapshot buffer, interpolation in the
render path, prediction and reconciliation for the local player, and a shared
movement function used by both host and client.

---

## Verification

Measure, do not guess — "feels better" is not evidence.

1. Console clean.
2. **Baseline first.** Record input-to-visible-response latency from T30's
   measurement before changing anything.
3. **Prediction reduces perceived latency.** Measure again; local input should
   appear to take effect within one frame. Report both numbers.
4. **Remote motion is smooth** at 30 Hz snapshots — no visible stepping.
5. **Reconciliation is invisible under good conditions.** At <50ms RTT with no
   loss, the local head must not visibly jitter or snap. Watch a straight run and
   a hard turn for 60 seconds each.
6. **Divergence is handled.** Inject 200ms latency and 5% loss; the local head
   may correct visibly, but must never oscillate or run away.
7. **No predicted deaths.** Force a near-miss under high latency and confirm the
   client never shows a death that the host did not decide. Run 10 trials.
8. **Traces still match** between host and client after prediction — replay must
   not double-append trace points, which is the classic bug here. Compare point
   counts.
9. **Single-player unaffected.** Prediction code must be inert offline. Full
   regression sweep, §7.6.

## Definition of done

- [ ] Remote players interpolated with a ~100ms render delay; angle wrapping correct
- [ ] Local head predicted, reconciled by rewind-and-replay against acked input
- [ ] One shared movement implementation used by host and client
- [ ] Death, collection and effects never predicted
- [ ] Latency before/after reported
- [ ] No trace double-append after replay, verified by point count
- [ ] Behaviour under 200ms/5% loss documented
- [ ] `docs/TASKS.md`: T31 → `DONE`; T32 → `READY`
