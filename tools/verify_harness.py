"""Reusable browser-verification harness for Cellular Zatacka.

Every task's "## Verification" section needs the same scaffolding: a served
copy of the game, a Chromium that actually launches in this sandbox, console
error capture, and a way to advance game time. This module provides it so each
session does not re-derive it (and re-hit the same four traps).

Usage from a task's own short script:

    from verify_harness import game

    with game(players=1, bots=1) as g:
        g.run_game_seconds(30)
        print(g.evaluate("players.filter(p => p.alive).length"))
        g.screenshot("after30s")
        g.assert_console_clean()

Run it directly for a smoke test:  python3 tools/verify_harness.py

KEEP EVERY INVOCATION UNDER 10 MINUTES — that is the command ceiling in a
scheduled session. Split long checks into several short scripts.

## Budgeting game time (read before writing a check)

There is no GPU here, so WebGL runs in software and the game simulates SLOWER
THAN REAL TIME. Measured ratios of game-seconds per wall-second:

    1280x1024 ......... 0.11x   (disabling the bloom filter does not help --
                                 the cost is rasterisation, not the filter)
     640x480  ......... 0.38x

So the default viewport here is 640x480, and a 10-minute invocation buys you
roughly **3.5 minutes of game time**. Budget accordingly:

  - Use the default small viewport for anything measuring behaviour or numbers.
  - Pass width/height only for screenshots a human will look at, and keep those
    runs short.
  - A task asking for "5 minutes at Gen 2" or "10 minutes under the fuzzer"
    CANNOT be done in one invocation. Either split it across several scripts, or
    use the dev fast-forward (+15s of survivalTime per press) when the check is
    about elapsed game time rather than accumulated simulation steps. Say in
    your commit message which you did.
"""

import glob
import json
import os
import subprocess
import time
from contextlib import contextmanager

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = "260703_Cellsnake.html"
PORT = 8083
SHOT_DIR = "/tmp/verify"

# TRAP 1 — browser version skew. The image ships a pinned Chromium build while
# a pip-installed playwright expects a different one, so p.chromium.launch()
# fails with "Executable doesn't exist" and tells you to run `playwright
# install`. Do NOT run it (it needs blocked egress). Glob the preinstalled
# build instead.
def chromium_path():
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    raise RuntimeError("no preinstalled Chromium under /opt/pw-browsers")


# TRAP 2 — the browser always requests /favicon.ico, which the dev server 404s.
# That is the one expected console entry over http://. Everything else is a
# real failure. (Loading over file:// produces no such request at all.)
IGNORABLE = ("favicon.ico",)


class Game:
    def __init__(self, page, proc):
        self.page, self._proc = page, proc
        self.console_errors, self.page_errors = [], []
        page.on("console", self._on_console)
        page.on("pageerror", lambda e: self.page_errors.append(str(e)))

    def _on_console(self, m):
        if m.type != "error":
            return
        # The offending URL is in m.location, not m.text — the text is just
        # "Failed to load resource: ... 404". Check both or the filter misses.
        where = (m.location or {}).get("url", "") if hasattr(m, "location") else ""
        if any(s in m.text or s in where for s in IGNORABLE):
            return
        self.console_errors.append(f"{m.text} [{where}]" if where else m.text)

    def evaluate(self, expr):
        return self.page.evaluate(expr if expr.strip().startswith("(")
                                  else f"() => ({expr})")

    # TRAP 3 — startRound() reads its configuration from the DOM <select>
    # elements, NOT from the currentMode / aiCount globals. Assigning those
    # globals and calling startRound() silently gives you the previous config —
    # you think you have a bot and you do not. Always set the selects.
    def start_round(self, players=1, bots=1, camera="shared", speed="1.5"):
        self.page.evaluate("""(cfg) => {
            document.getElementById('modeSelect').value   = String(cfg.players);
            document.getElementById('aiSelect').value     = String(cfg.bots);
            document.getElementById('cameraSelect').value = cfg.camera;
            document.getElementById('speedSelect').value  = cfg.speed;
            updateUI();
            startRound();
        }""", {"players": players, "bots": bots, "camera": camera, "speed": speed})

    # TRAP 4 — software rendering means game time runs SLOWER than wall time
    # (~0.38x at 640x480). Never sleep a fixed wall-clock duration and assume
    # game time passed. Poll the game's own clock.
    #
    # TRAP 5 — the round can END underneath you, which freezes survivalTime and
    # would spin this loop until it times out. That is exactly what happens with
    # players=1, bots=1: nobody presses a key for the human, it drives straight
    # into the membrane, and with only the bot left the round is over in a few
    # seconds. Either pass immortal=True, or use enough bots that the round
    # survives (players=1, bots=3). This raises immediately instead of hanging.
    def run_game_seconds(self, seconds, timeout=540):
        start = self.evaluate("survivalTime")
        t0 = time.time()
        while True:
            elapsed = self.evaluate("survivalTime") - start
            if elapsed >= seconds:
                return elapsed
            if not self.evaluate("isPlaying"):
                raise RuntimeError(
                    f"round ended after {elapsed:.1f}s of the {seconds}s requested "
                    f"({self.stats()}). Pass immortal=True or add more bots.")
            if time.time() - t0 > timeout:
                raise TimeoutError(
                    f"only {elapsed:.1f}s of game time in {timeout}s wall clock. "
                    f"At ~0.38x you get ~3.5 game-minutes per 10-minute invocation — "
                    f"split this check into several scripts.")
            self.page.wait_for_timeout(250)

    # T22 step 7: drives window.stepHeadless() directly instead of polling
    # survivalTime over wall-clock ticks -- no rendering happens at all, so
    # there is no TRAP-4-style ratio to wait out.
    def run_headless_seconds(self, seconds, dt=1 / 60):
        start = self.evaluate("survivalTime")
        t0 = time.time()
        self.evaluate(f"() => window.stepHeadless({seconds}, {dt})")
        wall = time.time() - t0
        elapsed = self.evaluate("survivalTime") - start
        return elapsed, wall

    def stats(self):
        return self.evaluate("""{
            players: players.length,
            bots: players.filter(p => p.isBot).length,
            alive: players.filter(p => p.alive).length,
            botsAlive: players.filter(p => p.isBot && p.alive).length,
            survivalTime: +survivalTime.toFixed(1),
            tracePoints: players.reduce((a,p) => a + p.traceSegments.reduce((b,s) => b+s.length, 0), 0),
            organelles: organelles.length,
            vesicles: vesicles.length,
            worldChildren: world.children.length,
            gridCells: typeof spatialGrid !== 'undefined' ? spatialGrid.cells.size : null,
            fuzzStats: typeof window.fuzzStats !== 'undefined' ? window.fuzzStats : null
        }""")

    def screenshot(self, name):
        os.makedirs(SHOT_DIR, exist_ok=True)
        path = f"{SHOT_DIR}/{name}.png"
        self.page.screenshot(path=path)
        return path  # inspect it with the Read tool — Read renders images

    def assert_console_clean(self):
        if self.console_errors or self.page_errors:
            raise AssertionError(json.dumps(
                {"console": self.console_errors, "page": self.page_errors}, indent=2))


@contextmanager
def game(players=1, bots=1, camera="shared", speed="1.5", autostart=True,
         immortal=False, use_file_protocol=False, width=640, height=480):
    """immortal=True disables death checks so a round can be observed for as
    long as you like. It sets godMode if that flag exists (post-T04) and falls
    back to devMode otherwise (pre-T04, where devMode is still overloaded).
    Never use it for a check that is ABOUT collisions."""
    from playwright.sync_api import sync_playwright

    proc = None
    if not use_file_protocol:
        proc = subprocess.Popen(["python3", "-m", "http.server", str(PORT)],
                                cwd=REPO, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    url = (f"file://{REPO}/{GAME}" if use_file_protocol
           else f"http://localhost:{PORT}/{GAME}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=chromium_path(),
            args=["--no-sandbox", "--enable-precise-memory-info"])
        page = browser.new_page(viewport={"width": width, "height": height})
        g = Game(page, proc)
        try:
            page.goto(url)
            page.wait_for_function("typeof PIXI !== 'undefined' && typeof world !== 'undefined'",
                                   timeout=15000)
            page.wait_for_timeout(1500)
            if immortal:
                page.evaluate("() => { if (typeof godMode !== 'undefined') "
                              "{ godMode = true; } else { devMode = true; } }")
            if autostart:
                g.start_round(players, bots, camera, speed)
            yield g
        finally:
            browser.close()
            if proc:
                proc.terminate()


if __name__ == "__main__":
    with game(players=1, bots=3, immortal=True) as g:
        elapsed = g.run_game_seconds(10)
        out = {"smoke": "ok", "gameSecondsElapsed": round(elapsed, 1), **g.stats()}
        out["pixi"] = g.evaluate("PIXI.VERSION")
        out["bloom"] = g.evaluate("typeof PIXI.filters.AdvancedBloomFilter !== 'undefined'")
        out["consoleErrors"] = g.console_errors
        out["pageErrors"] = g.page_errors
        print(json.dumps(out, indent=2))
