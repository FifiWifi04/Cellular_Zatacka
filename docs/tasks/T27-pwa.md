# T27 — Installable PWA (offline, home-screen, fullscreen)

**Track:** H (Phase 6) · **Depends on:** T26 · **Risk:** low · **Est. diff:** ~80 lines + 2 small files

Read `docs/AGENT_CONDUCT.md` before starting.

---

## Goal

Make the game installable to a phone's home screen, launching fullscreen and
working with no network — without an app store, a build step, or a rewrite.

## Why

This is the cheapest possible answer to "can it be an app?". A Progressive Web
App gives you the home-screen icon, the fullscreen launch and offline play for
about eighty lines. Since T-vendoring put PixiJS in `vendor/`, the game already
has **no runtime network dependency at all** — the hard part of offline support
is already done.

Store distribution (Capacitor/Cordova wrapping) is a separate, larger decision
and is explicitly **not** in this task.

---

## Design

### 1. Web app manifest

Add `manifest.webmanifest` beside the HTML and link it:

```
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#0d0d1a">
```

Contents: `name`, `short_name`, `start_url: "."`, `display: "fullscreen"`,
`orientation: "any"` (see T23 — do not hard-lock), `background_color` and
`theme_color` matching the game's `#0d0d1a`, and an `icons` array.

**Icons must be real files**, at minimum 192×192 and 512×512 PNG, plus a
`maskable` variant so Android does not letterbox it. Generate them from the
game's own aesthetic — a glowing cell on the dark background. Keep them small.

### 2. Service worker

Add `sw.js` with a **cache-first** strategy over a small explicit precache list:
the HTML, `vendor/pixi.min.js`, `vendor/pixi-filters.js`, the manifest and the
icons. That is the whole app.

Rules that matter:
- **Version the cache name** (e.g. `cellular-zatacka-v1`) and delete old caches
  in `activate`. Without this, players get a stale game forever after the first
  visit — the single most common PWA failure.
- Bump that version whenever the game file changes. Note it in
  `AGENT_CONDUCT.md` so future tasks remember.
- Register the worker only when `'serviceWorker' in navigator`, and **only over
  https or localhost** — it silently does nothing over `file://`, which must
  remain a supported way to run the game.

### 3. Do not break `file://`

The offline-from-`file://` property is a stated constraint
(`AGENT_CONDUCT.md` §2) and this task must not regress it. The manifest link and
the worker registration must both fail gracefully when the page is opened
directly from disk. Verify explicitly — see Verification 6.

### 4. Update prompt

When the worker detects a new version, show a small unobtrusive "new version
available — tap to reload" affordance rather than reloading underneath the
player. Reloading mid-round would be hostile.

---

## Files touched

- `260703_Cellsnake.html` — manifest link, theme-color meta, worker registration
- `manifest.webmanifest` (new)
- `sw.js` (new)
- `icons/` (new — 192, 512, maskable)

This is the second exception to the single-file rule, after `vendor/` and
`tools/`. A PWA cannot be a single file; the manifest and worker must be separate
fetchable resources. Note that in `AGENT_CONDUCT.md` §2.

---

## Verification

1. Console clean; no service-worker registration errors.
2. **Installable.** In Chromium DevTools → Application → Manifest, the manifest
   parses with no warnings and the install criteria are met.
3. **Offline works.** Load over http, then stop the server, then reload. The game
   must start and be fully playable. This is the headline test.
4. **Cache versioning.** Change the cache name, reload twice, and confirm the old
   cache is deleted in `activate` (check Application → Cache Storage).
5. **Stale-content check.** Modify the HTML, bump the version, reload — the new
   content appears rather than the cached old one.
6. **`file://` still works.** Open the HTML directly from disk. The game must run
   with a completely clean console — no failed manifest fetch, no worker error.
7. **Fullscreen launch.** Install to home screen in an emulated mobile context and
   confirm it launches without browser chrome.
8. **Desktop unaffected.** A normal desktop browser session behaves exactly as
   before.

## Definition of done

- [ ] Manifest with 192/512/maskable icons, parsing cleanly
- [ ] Cache-first service worker with a versioned cache and old-cache cleanup
- [ ] Offline play verified with the server stopped
- [ ] `file://` still runs with a clean console
- [ ] Update prompt rather than a forced reload
- [ ] `AGENT_CONDUCT.md` §2 notes the new files and the cache-bump requirement
- [ ] `docs/TASKS.md`: T27 → `DONE` — Phase 6 complete
