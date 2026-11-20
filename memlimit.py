# Memory guard for every Python script of this repo (user, 2026-11-20: "Require all scripts to
# respect memory limits", after a run exhausted the 31 GB machine).
#
# A daemon thread watches the process's anonymous resident memory (RssAnon in /proc/self/status:
# heap, numpy arrays; not file-backed pages, so memory-mapped .npy files and the LMDB dump do not
# count) and stops the script with a message once it passes the limit:
#   first KeyboardInterrupt in the main thread (finally blocks and context managers run), then,
#   GRACE seconds later, a hard exit with status 137.
#
# Limit: GLOBASA_MEM_GB (GB, float), default DEFAULT_SHARE of the machine's RAM;
#        GLOBASA_MEM_GB=0 switches the guard off for one run.
# Per process: multiprocessing workers each get their own guard, so size pools accordingly.
#
# Not imported by hand: install() writes a one-line globasa_memlimit.pth into venv/'s
# site-packages (every venv python, even with -I; a sitecustomize.py there is shadowed by
# Ubuntu's /usr/lib/python3.10/sitecustomize.py) and one into the user site of the system
# python3 that only acts for scripts inside this repo (not under -I / -s, which skip the user site).
# setup.sh calls install(); to (re)install by hand:
#   venv/bin/python -c "import memlimit; memlimit.install()"
import os
import sys
import threading
import time

REPO = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SHARE = 0.4
POLL = 0.1
GRACE = 5.0
MARK = "# GlobasaLexiTools memlimit guard"


def _status_kb(field, path="/proc/self/status"):
    with open(path) as f:
        for line in f:
            if line.startswith(field + ":"):
                return int(line.split()[1])
    return 0


def limit_bytes():
    env = os.environ.get("GLOBASA_MEM_GB")
    if env is not None:
        return int(float(env) * 1024 ** 3)
    return int(_status_kb("MemTotal", "/proc/meminfo") * 1024 * DEFAULT_SHARE)


def rss_anon():
    return _status_kb("RssAnon") * 1024


def start(only_repo=False):
    if only_repo and not _in_repo():
        return
    if getattr(sys, "_globasa_memlimit", False) or not os.path.exists("/proc/self/status"):
        return
    limit = limit_bytes()
    if limit <= 0:
        return
    sys._globasa_memlimit = True

    def watch():
        import _thread
        while True:
            used = rss_anon()
            if used > limit:
                sys.stderr.write(
                    f"\nmemlimit: {used / 1024 ** 3:.1f} GB anonymous memory > limit {limit / 1024 ** 3:.1f} GB; "
                    f"stopping {sys.argv[0] or 'python'} (load less, stream or chunk; "
                    f"GLOBASA_MEM_GB=<GB> changes the limit)\n")
                sys.stderr.flush()
                _thread.interrupt_main()
                time.sleep(GRACE)
                os._exit(137)
            time.sleep(POLL)

    threading.Thread(target=watch, name="memlimit", daemon=True).start()


def _in_repo():
    paths = [os.getcwd()] + [os.path.abspath(a) for a in sys.argv[:1] if a and a != "-c"]
    return any(p == REPO or p.startswith(REPO + os.sep) for p in paths)


def install():
    import site
    venv_site = [p for p in site.getsitepackages() if p.startswith(os.path.join(REPO, "venv"))]
    line = (f"import sys; sys.path.insert(0, {REPO!r}); import memlimit; sys.path.pop(0); "
            f"memlimit.start({{}})  {MARK}\n")
    targets = [(os.path.join(p, "globasa_memlimit.pth"), line.format("")) for p in venv_site[:1]]
    targets.append((os.path.join(site.getusersitepackages(), "globasa_memlimit.pth"), line.format("only_repo=True")))
    for path, text in targets:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        print(f"memlimit: wrote {path}")
