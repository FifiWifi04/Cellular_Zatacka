# T36 — Target mode: inconsistent legend, and attack mode barely does anything

**Track:** J · **Depends on:** — · **Risk:** medium (gameplay)

Read `docs/AGENT_CONDUCT.md`.

## Two related complaints

> "The legend for toggling between green and red of the head of the snake is not
> consistent."

> "Before, when switching to red and getting a speed boost, it would give it to
> the opponent."

## What the code does now

`controlsText` says:

```
3rd Key: Toggle Boost Target (Green=Self, Red=Attack)
```

But searching `targetMode === 'attack'` finds it consulted in **exactly one
gameplay place**: the malignant-mass shatter (T14, Gen 3+). Nothing in the
vesicle-collection path branches on it.

So the legend promises a "boost target" choice that the current build does not
implement — and the behaviour the owner remembers (red = the pickup's effect goes
to your opponent instead of you) is **absent**. Whether it was lost in a refactor
or never fully built, the label and the behaviour disagree.

## Step 1 — establish the truth, before designing

Search the git history for when a `targetMode` branch existed in the vesicle
collection block (`git log -S "targetMode" -- 260703_Cellsnake.html`). Record in
`## Findings` whether it was removed, and in which commit. That decides whether
this is a regression to restore or a feature to build.

## Step 2 — restore the mechanic

Make `targetMode` mean what the label says, in the vesicle pickup path:

- **`self` (green)** — the pickup's effect applies to you. Current behaviour.
- **`attack` (red)** — the effect is applied to an **opponent** instead. Choose
  the target deterministically and document it (nearest living opponent is the
  obvious rule). With no opponent alive, fall back to `self` so the pickup is
  never simply wasted.

Which effects transfer is a design call — make it, state it in `## Findings`, and
keep it simple. A defensible default: beneficial effects (speed, ghost, hunter)
transfer; harmful/neutral ones do not.

Keep the Gen 3+ mass-shatter behaviour exactly as it is.

## Step 3 — make the legend honest

One sentence that describes what actually happens, shown in both the menu
(`controlsText`) and T20's control splash, generated from one string so they
cannot drift. The head aura already colours green/red — make the wording match
the colours exactly.

## Findings

**Step 1 — was this a regression?** No. `git log -S "targetMode" -- 260703_Cellsnake.html`
returns exactly 4 commits: `4bf057f` (initial upload), `aa74cac` (T04), `d434759`
(T14), `9549a46` (T23). None of them removed a `targetMode` branch from the
vesicle-pickup path — the mitochondria (speed) branch that does opponent
targeting has existed **unchanged since the very first commit**. It was never
lost; it was always broken. The task's own search for the literal string
`targetMode === 'attack'` (Step 1's own diagnostic) missed it because that
branch was written as `if (p.targetMode === 'self' || ...) { self } else {
opponent }` — the inverse of what the grep was looking for.

The actual bug: the branch was gated by `p.targetMode === 'self' || currentMode
=== 1`. `currentMode` is the *human player count* selector (1-4), not "no
opponents alive". In the most common configuration — **Solo vs Bots**
(`currentMode === 1`, `aiCount >= 1`, i.e. Quick Play) — this forced every
pickup to self regardless of the toggle, even though `controlsText` (shown for
`totalPlayers >= 2`, which Solo-vs-Bots satisfies) promised "Red = Attack".
That's exactly the owner's complaint 2. It also means the malformed legend
(complaint 1) had two different, both-wrong descriptions in two places: the
menu said "Toggle Boost Target (Green=Self, Red=Attack)" with no explanation,
while the control splash's static hint said red meant "shatter structures" —
describing only the T14 malignant-mass side effect and not mentioning boost
redirection at all.

**Step 2 — design decisions.**
- *Which effects transfer:* all three vesicle types transfer wholesale
  (mitochondria/speed, membrane/ghost, lysosome/hunter) — the task's suggested
  default. Kept simple by extracting one `boostTarget(p)` helper (defined next
  to `deleteOldestTrace`) that returns either `p` or an opponent, computed once
  per pickup event, then routing every `p.effects.*` / `p.traceSegments`
  reference in the three type blocks through that single `target` instead.
  This is a straightforward generalisation of the mitochondria block's
  pre-existing `targets.forEach` pattern (now simplified to a single `target`,
  since there is only ever one).
- *Target selection:* nearest living opponent by Euclidean distance, not the
  old random pick, per the task's explicit "choose deterministically" ask.
- *No living opponent:* falls back to `p` itself (`boostTarget` returns `p`
  when `opponents.length === 0`), so attack mode never wastes a pickup — this
  covers both a truly solo round (no bots at all) and every bot/opponent being
  dead.
- Gen 3+ malignant-mass shatter-on-attack (T14) is untouched — it reads
  `p.targetMode` directly and was not part of this change.

## Verification

1. Console clean.
2. `## Findings` states whether this was a regression, with the commit.
3. In `self` mode, effects apply to you — unchanged from today.
4. In `attack` mode, a speed pickup demonstrably lands on an opponent: log both
   players' `effects.speedTimer` before and after.
5. Solo, `attack` mode falls back to `self`; the pickup is never wasted.
6. Legend text matches behaviour in both places.
7. Bots: confirm `updateBotAI` still sets `targetMode` sensibly and does not
   grief itself.
8. Regression sweep §7.6.
