# T54 — Persist runs and show a high-score table

**Track:** L (Phase 8) · **Depends on:** T53 · **Risk:** low-medium (first persisted state) · **Est. diff:** ~120 lines

Read [`docs/PHASE8-META-PROGRESSION.md`](../PHASE8-META-PROGRESSION.md).

T53 produces a score and a stats card that vanish when the round ends. This makes
them stick, and gives the owner the thing actually asked for: *"players can see
their high-scores with different statistics."*

---

## Design

### 1. Storage

`localStorage`, one key, JSON, **with a schema version from the first commit**:

```json
{ "v": 1, "runs": [ { "score": 0, "time": 0, "gen": 1, "stats": {…}, "at": 0, "mode": "…" } ], "totals": {…} }
```

- **Cap the history** (`HISTORY_MAX`, e.g. 50 runs). Unbounded growth in
  `localStorage` will eventually throw, and it throws on write — mid-game.
- **Every access must be wrapped.** Private browsing, a disabled-storage policy
  and a full quota all throw on read *or* write. A failure must degrade to
  "no history this session" and the game must play normally. Test it by stubbing
  `localStorage.setItem` to throw — do not assume.
- **Unknown/newer `v` → ignore and start fresh**, never crash and never silently
  reinterpret another version's shape.
- Corrupt JSON → same. Wrap `JSON.parse` in try/catch.

### 2. What the table shows

Top N by score, plus lifetime totals (rounds played, best generation reached,
total vesicles, total breaks, longest survival). Both the per-run *and* the
aggregate view — the owner asked for "different statistics", not one number.

Records should be per **mode** where it matters: a Quick Play 1v1 and a 4-player
round are not comparable. Store `mode` per run and either filter or label.

### 3. Where it lives

A panel reached from the main menu, built the same way as T41's help overlay —
which already solves the layout, the close button, the outside-click close, and
(after T46) the pause interaction. **Reuse that structure**; do not invent a
third overlay pattern.

A new high score should be called out on the end-of-round card. That moment is
the payoff.

### 4. Clearing

The player must be able to wipe their history, with a confirmation step. It is
their data on their device; do not make it unclearable.

## Verification

1. Console clean.
2. A completed run appears in the table; reload the page and it is still there.
3. **Storage failure is survivable** — stub `setItem` to throw, play a full
   round, confirm the game does not break and the failure is not spammed to the
   console every frame.
4. **Corrupt data is survivable** — write garbage into the key, reload, confirm a
   clean start rather than a crash.
5. **Wrong version is survivable** — write `{"v":99}`, reload, same.
6. `HISTORY_MAX` holds: play/simulate more runs than the cap, confirm the oldest
   drop and the payload stays bounded. State the stored byte size.
7. Table renders at 390×844, 844×390 and 1280×800; screenshot each.
8. Clearing works, and asks first.
9. New-high-score callout fires exactly when the score is a new best, and not
   otherwise.
10. Regression sweep §7.6.

## Definition of done

- [ ] Versioned, capped, wrapped `localStorage` persistence
- [ ] Per-run table **and** lifetime totals, mode-aware
- [ ] Reuses the T41 overlay structure
- [ ] All three failure modes (throw, corrupt, wrong version) proven survivable
- [ ] Clear-history with confirmation
- [ ] `docs/TASKS.md`: T54 → `DONE`, T55 → `READY`

---

## Findings

*(Stored schema, byte size at the cap, and how each failure mode was induced and
verified.)*
