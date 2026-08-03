# Cellular Zatacka — development docs

Start here.

| File | What it is |
|---|---|
| [`AGENT_CONDUCT.md`](AGENT_CONDUCT.md) | **Read first, every session.** Rules, the five traps in this codebase, verification requirements, definition of done. |
| [`TASKS.md`](TASKS.md) | The task board. Statuses, dependencies, and a snapshot of the current state of the code. |
| [`tasks/`](tasks/) | One file per task, in execution order. Each is self-contained. |
| [`BACKLOG.md`](BACKLOG.md) | Incidental findings. Append here instead of fixing things outside your task. |
| [`SESSION_PROMPT.md`](SESSION_PROMPT.md) | Copy-paste prompt for a scheduled/routine agent session. |
| `reports/` | Created by T06a/T06b — soak data and the Phase 1 gate report. |

Project-level context lives in the repository root:
`Development_plan.md` (the 5-phase roadmap) and `walkthrough.md` (history — note
that its Phase 2 section describes work that is **not** in the current code; see
[`tasks/P01-asset-pipeline-parked.md`](tasks/P01-asset-pipeline-parked.md)).

---

## The rules in one screen

1. **One task per session.** Lowest-numbered `READY` task on the board. Nothing else.
2. **Smallest possible diff.** No reformatting, no renaming, no drive-by fixes.
3. **Every hazard goes in two places** — `checkCollision()` *and* `raycast()`.
4. **Collision is always swept**, never point-in-time.
5. **Physics state is authoritative**; sprites mirror it and never own it.
6. **No allocation in the per-frame hot path.**
7. **Verify in a real browser** before committing. Console must be clean.
8. **Found something else?** `BACKLOG.md`. Do not fix it.

---

## Task file anatomy

Every task file has the same sections, in this order:

- **Goal** — one sentence
- **Why** — the actual defect or requirement, with evidence from the code
- **Prerequisites** — what to read before writing anything
- **Design / Implementation plan** — the approach, with the decisions already made
- **Files touched** — the exact call sites
- **Verification** — numbered, concrete, must all pass
- **Definition of done** — the checklist to tick before committing

Where a task needs information only obtainable by reading the code, it has a
**`## Findings`** section to fill in *before* implementing. Those are not
optional — they are the questions whose answers change the design.

---

## Execution order at a glance

```
Track A  T01 → T02 → T03          finish Phase 1's bot + sensor
         T04, T05 → T06a → T06b   finish Phase 1's fuzzer, evidence, then the verdict
Track B  T07 → T08, T09, T10      structural hygiene
Track C  T11 → T12/T13/T14/T15    Phase 3 generation-gated content
Track D  T16 → T17/T18            Phase 4 juice
Track E  T19, T20                 Phase 5 UX
Track F  T21                      Phase 2.2 additive blending (vector renderer)
Track G  T22                      sim/render split — enables Phase 7, speeds up tests
Track H  T23 → T24 → T25 → T26 → T27    Phase 6 mobile (independent of everything)
Track I  T28 → T29 → T30 → T31 → T32    Phase 7 multiplayer (needs T22)
```

**T09, T20, T21, T23, and T05 are independent** — take one of those if the head
of a track is blocked. **T23 opens all of Phase 6**, which depends on nothing and
can run in parallel with Phase 1–5 work.

Phase 2.1 (the sprite/asset swap) is **parked** — see
[`tasks/P01-asset-pipeline-parked.md`](tasks/P01-asset-pipeline-parked.md). Phase
2.2 is not: it is T21, and it works on the current vector renderer.

**Phase 1 is not signed off until T06b returns a PASS.** Track C and D depend on
**T06a** (the evidence) rather than on the verdict, so the routine keeps moving
while the report waits for you — but a FAIL means revisiting whatever landed in
that window.
