"""Run a command with a hard memory cap on its whole process tree.

memlimit.py guards repo Python processes only; the web tests also run Node (wasm,
Pyodide) and native Apertium tools. 2026-11-26 an uncapped native rtx-proc pushed the
machine into swap and it had to be rebooted, so every web test runs through this:

    python3 web/test/capped.py node web/test/parity.mjs ...

The command gets its own process group; the summed RSS of the group is checked every
0.2 s and the group is killed (SIGKILL) as soon as it passes GLOBASA_MEM_GB (GB,
default 40% of RAM, the same default as memlimit.py). Exit status 137 = killed by the cap.
"""
import os
import signal
import subprocess
import sys
import time


def limit_bytes():
    env = os.environ.get("GLOBASA_MEM_GB")
    if env:
        return int(float(env) * 1024 ** 3)
    with open("/proc/meminfo") as f:
        total_kb = int(next(line for line in f if line.startswith("MemTotal:")).split()[1])
    return int(total_kb * 1024 * 0.4)


def group_rss(pgid):
    total = 0
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/stat") as f:
                fields = f.read().rsplit(")", 1)[1].split()
            if int(fields[2]) != pgid:          # field 5 (pgrp), after state and ppid
                continue
            with open(f"/proc/{pid}/statm") as f:
                total += int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
        except (OSError, IndexError, ValueError):
            continue
    return total


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cap = limit_bytes()
    proc = subprocess.Popen(sys.argv[1:], start_new_session=True)
    peak = 0
    while proc.poll() is None:
        rss = group_rss(proc.pid)
        peak = max(peak, rss)
        if rss > cap:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            print(f"capped.py: killed {' '.join(sys.argv[1:3])}: {rss / 1024 ** 3:.1f} GB > cap "
                  f"{cap / 1024 ** 3:.1f} GB (GLOBASA_MEM_GB)", file=sys.stderr)
            sys.exit(137)
        time.sleep(0.2)
    print(f"capped.py: peak {peak / 1024 ** 3:.2f} GB of {cap / 1024 ** 3:.1f} GB cap", file=sys.stderr)
    sys.exit(proc.returncode)


main()
