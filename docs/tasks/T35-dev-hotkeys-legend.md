# T35 — Dev hotkeys: drop `[`/`]`, make the legend match reality

**Track:** J · **Depends on:** — · **Risk:** very low

Read `docs/AGENT_CONDUCT.md`.

## The bug

> "Legend when turning the dev mode is not consistent with the actual keys. I
> would like to not have `[` and `]` as they are difficult to press, `Tab` for
> +15 s, and a different key binding for changing Generation."

`[` and `]` require AltGr on Nordic and several European layouts — genuinely
awkward. The on-screen legend also does not match what the handler does.

## Required map

| Key | Action |
|---|---|
| `` ` `` / `~` / `½` | toggle dev mode (master) |
| **`Tab`** | **+15 s** — already works; make it the only binding, drop `]` |
| **`G`** | god mode |
| **`F`** | fuzzer |
| **`N`** | **+1 generation** — replaces `[` (mnemonic: Next generation) |
| `K` | screenshake off/on |
| `,` `.` | whatever they currently do — read the handler and either document them in the legend or remove them |

**Verify `N` and every key you keep against all four `playerConfigs` entries**
before committing — P3 uses `G`/`J`/`H`, so dev keys must stay gated on `devMode`
being on. Read the configs; do not trust this table.

## Also

- Rewrite the legend panel so **every line matches the handler**, generated from
  a single key-map object rather than hand-written strings — that is why they
  drifted apart.
- Update `Development_plan.md`'s "Dev Mode Active" line to match.
- Keep `Tab`'s `preventDefault()` conditional on dev mode being on.

## Verification

1. Console clean.
2. Every key in the legend does exactly what the legend says. Test all of them.
3. `[` and `]` do nothing.
4. 4-player round with dev mode on: P3's `G`/`J`/`H` steer P3 and do not fire dev
   actions.
5. `Tab` does not break page tab-navigation when dev mode is off.

## Findings

Checked the required map against `playerConfigs` (§ "Verify `N` and every key...")
before implementing, per this task's own instruction not to trust the table:

- P3's config is `{ left: 'g', right: 'j', leftAlt: 'G', rightAlt: 'J', toggle: 'h',
  toggleAlt: 'H' }`. `keys['G']` is live continuously in `gameLoop` (P3's steer-left
  alt), not just on the one-shot `keydown`. Binding god mode to `G` as the table
  suggests would toggle god mode every time P3 turns left with Shift/Caps held --
  exactly the failure verification item 4 tests for.
- Kept god mode on `,` (its existing free-key binding, already collision-free)
  instead of moving it to `G`. This is a deliberate deviation from the "G | god
  mode" row; every other row in the required map (`Tab`, `F`, `N`, `K`) was free
  of collisions and implemented as specified. `,` and `.` are documented in the
  regenerated legend per the task's own fallback ("either document them ... or
  remove them").
- `N`/`n` (+1 generation) and `Tab`-only (+15s, `]` dropped) have no collisions
  with any of the four `playerConfigs` entries (`ArrowLeft/Right/Down`,
  `a/d/A/D/s/S`, `g/j/G/J/h/H`, `4/6/5`).
