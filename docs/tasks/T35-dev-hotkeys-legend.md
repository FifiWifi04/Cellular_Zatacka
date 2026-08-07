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
