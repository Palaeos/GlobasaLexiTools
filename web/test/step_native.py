"""The eng->glb Python steps under native CPython, on the exact streams the browser gave them
(saved by step_timing.mjs ... SAVE_DIR): Pyodide's time vs CPython's per step, the wasm penalty.
Neural steps (pos/coref/parse/focus) need an NLP service natively and are skipped; their
Pyodide profile (step_timing.mjs profile) shows where their time goes.

    python3 web/test/capped.py python3 web/test/step_native.py SAVE_DIR
"""
import glob
import json
import os
import subprocess
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "GlobasaTranslation")
NEURAL = {"pos", "coref", "parse", "focus"}
REPEAT = 3


def native(p):
    return os.path.join(ROOT, p[len("/p/"):]) if p.startswith("/p/") else p


def run(cmd, stream, env):
    t0 = time.perf_counter()
    r = subprocess.run(cmd, input=stream, capture_output=True, text=True, env=env)
    return time.perf_counter() - t0, r


t0 = time.perf_counter()
subprocess.run([sys.executable, "-I", "-c", "pass"])
startup = time.perf_counter() - t0
print(f"CPython {sys.version.split()[0]} start-up: {startup * 1000:.0f} ms")
print(f"{'step':40} {'Pyodide':>9} {'CPython':>9} {'ratio':>6}")
tot_py = tot_c = 0
for meta in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))):
    m = json.load(open(meta))
    if NEURAL & set(m["args"]):
        print(f"{m['key'][:40]:40} {m['pyodide_ms'] / 1000:8.1f}s {'(neural, skipped)':>16}")
        continue
    stream = open(meta[:-5] + ".stream", encoding="utf-8").read()
    env = dict(os.environ, **{k: str(v) for k, v in m["env"].items()})
    cmd = [sys.executable, "-I", native(m["path"])] + [native(a) for a in m["args"]]
    best = None
    for _ in range(REPEAT):
        secs, r = run(cmd, stream, env)
        if r.returncode:
            print(f"{m['key'][:40]:40} failed: {r.stderr.strip().splitlines()[-1:]}")
            break
        best = secs if best is None else min(best, secs)
    if best is None:
        continue
    tot_py += m["pyodide_ms"] / 1000
    tot_c += best
    print(f"{m['key'][:40]:40} {m['pyodide_ms'] / 1000:8.1f}s {best:8.2f}s {m['pyodide_ms'] / 1000 / best:5.1f}x")
print(f"{'non-neural steps':40} {tot_py:8.1f}s {tot_c:8.2f}s {tot_py / max(tot_c, 1e-9):5.1f}x")
