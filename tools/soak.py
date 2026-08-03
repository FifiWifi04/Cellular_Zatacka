"""Long-running soak driver for the Phase 1 gate (T06a).

Runs the game under the fuzzer and samples window.fuzzStats until a target
number of ROUNDS has completed, writing every sample to CSV as it goes.

Why rounds and not minutes: what proves there is no display-object or memory
leak is many startRound() cycles, not wall-clock time. Rounds are also the only
target that stays meaningful across machines of different speed — this sandbox
has no GPU and simulates at roughly 0.11x-0.38x real time depending on viewport.

    python3 tools/soak.py A --rounds 60
    python3 tools/soak.py B --rounds 40 --minutes-cap 45
    python3 tools/soak.py --list

Run it DETACHED so it is not killed by the 10-minute foreground command cap:

    nohup python3 tools/soak.py A --rounds 60 > /tmp/soak-A.log 2>&1 &

Then poll `docs/reports/soak-A/soak.csv` (it is flushed every sample) and wait
for `docs/reports/soak-A/COMPLETE` to appear. A run WITHOUT that marker is
truncated: delete the directory and start it again. Never analyse a partial run.
"""

import argparse
import csv
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_harness import REPO, game  # noqa: E402

# Each config targets a different failure mode. Keep these in step with the
# table in docs/tasks/T06a-soak-measurement.md.
CONFIGS = {
    # label: (players, bots, camera, speed, immortal, why)
    "A": (1, 3, "shared", "1.5", False,
          "the real soak - players die and rounds cycle constantly"),
    "B": (1, 3, "shared", "3.5", True,
          "nothing dies, so traces grow unbounded - stresses the grid rebuild"),
    "C": (4, 0, "split", "1.5", False,
          "exercises the split-screen RenderTexture path"),
}

FIELDS = ["wall_s", "game_s", "rounds", "tracePoints", "gridCells", "worldChildren",
          "vesicles", "organelles", "virusParticles", "alive", "heapMB", "errors"]


def sample(g):
    return g.evaluate("""{
        game_s:        +survivalTime.toFixed(1),
        rounds:        (window.fuzzStats && window.fuzzStats.rounds) || 0,
        tracePoints:   players.reduce((a,p) => a + p.traceSegments.reduce((b,s) => b+s.length, 0), 0),
        gridCells:     typeof spatialGrid !== 'undefined' ? spatialGrid.cells.size : null,
        worldChildren: (function count(c){ return c.children.reduce((n,ch) => n + 1 + (ch.children ? count(ch) : 0), 0); })(world),
        vesicles:      vesicles.length,
        organelles:    organelles.length,
        virusParticles: (infection && infection.particles) ? infection.particles.length : 0,
        alive:         players.filter(p => p.alive).length,
        heapMB:        (performance.memory ? +(performance.memory.usedJSHeapSize/1048576).toFixed(1) : null),
        errors:        (window.fuzzStats && window.fuzzStats.errors) || 0
    }""")


def enable_fuzzer(g):
    """Turn the fuzzer on. Prefers the T04 flags; falls back to the pre-T04
    shape where devMode gates everything and 'f' is held rather than toggled."""
    return g.evaluate("""(() => {
        if (typeof fuzzActive !== 'undefined') { devMode = true; fuzzActive = true; return 'T04 flags'; }
        devMode = true; keys['f'] = true; return 'pre-T04 fallback (god mode also on)';
    })()""")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label", nargs="?", choices=sorted(CONFIGS))
    ap.add_argument("--rounds", type=int, default=60, help="target completed rounds")
    ap.add_argument("--minutes-cap", type=float, default=60.0,
                    help="wall-clock safety stop; a run that hits this is INCOMPLETE")
    ap.add_argument("--interval", type=float, default=10.0, help="seconds between samples")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list or not a.label:
        for k, v in sorted(CONFIGS.items()):
            print(f"{k}: players={v[0]} bots={v[1]} camera={v[2]} speed={v[3]} "
                  f"immortal={v[4]}\n   {v[5]}")
        return 0

    players, bots, camera, speed, immortal, why = CONFIGS[a.label]
    out = os.path.join(REPO, "docs", "reports", f"soak-{a.label}")
    if os.path.exists(os.path.join(out, "COMPLETE")):
        print(f"{out}/COMPLETE already exists — this run is done. Delete the "
              f"directory to redo it.")
        return 0
    os.makedirs(out, exist_ok=True)

    print(f"soak {a.label}: {why}\n  target={a.rounds} rounds  cap={a.minutes_cap}min  "
          f"viewport={a.width}x{a.height}", flush=True)

    t0 = time.time()
    deadline = t0 + a.minutes_cap * 60
    rows, last_shot, complete, abort = 0, 0.0, False, None

    with open(os.path.join(out, "soak.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        with game(players=players, bots=bots, camera=camera, speed=speed,
                  immortal=immortal, width=a.width, height=a.height) as g:
            mode = enable_fuzzer(g)
            print(f"  fuzzer: {mode}", flush=True)

            # PRECONDITION. Without T04 there is no window.fuzzStats, so
            # `rounds` would sit at 0 forever and the run would burn its whole
            # cap producing nothing. Fail in seconds instead of in an hour.
            if not g.evaluate("typeof window.fuzzStats !== 'undefined'"):
                abort = ("window.fuzzStats is missing — T04 (fuzzer hardening) has "
                         "not landed yet. This soak measures rounds completed and "
                         "cannot do that without it. Finish T04 first.")
            elif g.evaluate("typeof godMode === 'undefined'"):
                abort = ("godMode does not exist, so the fuzzer still runs with all "
                         "death checks disabled (the pre-T04 devMode overload). "
                         "Rounds would never cycle. Finish T04 first.")
            while not abort and time.time() < deadline:
                s = sample(g)
                s["wall_s"] = round(time.time() - t0, 1)
                w.writerow({k: s.get(k) for k in FIELDS})
                fh.flush()                      # survive a kill
                os.fsync(fh.fileno())
                rows += 1

                if s["errors"]:
                    print(f"  !! fuzzStats.errors={s['errors']} at {s['wall_s']}s", flush=True)
                if s["wall_s"] - last_shot >= 300:
                    g.screenshot(f"soak-{a.label}-{int(s['wall_s'])}s")
                    last_shot = s["wall_s"]
                if rows % 6 == 0:
                    print(f"  {s['wall_s']:7.0f}s wall  rounds={s['rounds']:4d}  "
                          f"children={s['worldChildren']:5}  heap={s['heapMB']}MB  "
                          f"errors={s['errors']}", flush=True)

                if s["rounds"] >= a.rounds:
                    complete = True
                    break

                # The round can end without the fuzzer restarting it (e.g. a
                # solo game-over stops the ticker). Nudge it rather than stall.
                if not g.evaluate("isPlaying"):
                    g.start_round(players, bots, camera, speed)

                g.page.wait_for_timeout(int(a.interval * 1000))

            final = sample(g)
            if not abort:
                g.screenshot(f"soak-{a.label}-final")

    if abort:
        # Leave nothing behind: a stale directory with a header-only CSV would
        # look like a real run to the next session.
        shutil.rmtree(out, ignore_errors=True)
        print(f"ABORT: {abort}", flush=True)
        return 2

    if complete:
        with open(os.path.join(out, "COMPLETE"), "w") as fh:
            json.dump({"label": a.label, "why": why, "config":
                       {"players": players, "bots": bots, "camera": camera,
                        "speed": speed, "immortal": immortal},
                       "target_rounds": a.rounds,
                       "wall_seconds": round(time.time() - t0, 1),
                       "samples": rows, "final": final,
                       "viewport": f"{a.width}x{a.height}",
                       "commit": os.popen("git -C %s rev-parse --short HEAD" % REPO).read().strip(),
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                      fh, indent=2)
        print(f"COMPLETE — {rows} samples, {final['rounds']} rounds, "
              f"{round(time.time()-t0)}s wall", flush=True)
        return 0

    print(f"INCOMPLETE — hit the {a.minutes_cap}min cap at {final['rounds']}/"
          f"{a.rounds} rounds. No COMPLETE marker written. Delete {out} and "
          f"re-run, or lower --rounds.", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
