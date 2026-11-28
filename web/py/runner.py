"""Runs the pairs' Python pipeline steps unchanged inside Pyodide (web/src/pipeline.mjs).

Each step is the same script the native mode runs (python3 -I script args): it reads
the stream from stdin and writes it to stdout. Here stdin/stdout/stderr are in-memory,
sys.argv and os.environ come from the manifest, and the compiled code is cached.

subprocess is replaced by a shim: the scripts only call subprocess.run() on
lt-proc / cg-proc / apertium-tagger (list form, or one shell pipeline), and those
calls go to the wasm tools through the synchronous JS bridge globasa_run_tool.

NLP requests to http://browser-nlp/ (the URL the page gives a neural client in place of
its local service) are answered from analyses the page computed in the browser
(add_analysis). The browser models run asynchronously, so a request with no analysis yet
raises NeedAnalysis (a BaseException, so the clients' "except Exception" fallback does
not swallow it); run_step reports it, the page analyses the text and runs the step again.
"""
import builtins
import io
import os
import shlex
import sys
import types

import json
import urllib.request

import js  # Pyodide: the worker's global scope

_code = {}
BROWSER_NLP = "http://browser-nlp/"
_analyses = {}                      # (url, text, chains wanted) -> JSON text, the last few
# BROWSER_NLP_COREF=1 in a step's environment (src/pipeline.mjs): the step reads coreference
# chains, so it must not get the chain-less analysis an earlier step (pos, parse) was given.
_KEEP = 8


class NeedAnalysis(BaseException):
    def __init__(self, url, text):
        super().__init__(url)
        self.url, self.text = url, text


def _key(url, text):
    return url, text, os.environ.get("BROWSER_NLP_COREF", "0")


def add_analysis(url, text, result_json, coref=False):
    _analyses[(url, text, "1" if coref else "0")] = result_json
    while len(_analyses) > _KEEP:
        del _analyses[next(iter(_analyses))]


class _Response:
    def __init__(self, body):
        self.body = body.encode("utf-8")

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _browser_open(req):
    url = req.full_url if hasattr(req, "full_url") else str(req)
    if not url.startswith(BROWSER_NLP):
        return None
    data = req.data if hasattr(req, "data") else None
    text = json.loads(data)["text"] if data else ""
    found = _analyses.get(_key(url, text))
    if found is None:
        raise NeedAnalysis(url, text)
    return _Response(found)


_real_build_opener, _real_urlopen = urllib.request.build_opener, urllib.request.urlopen


class _Opener:
    def __init__(self, real):
        self.real = real

    def open(self, req, *args, **kwargs):
        r = _browser_open(req)
        return r if r is not None else self.real.open(req, *args, **kwargs)


def _build_opener(*handlers):
    return _Opener(_real_build_opener(*handlers))


def _urlopen(req, *args, **kwargs):
    r = _browser_open(req)
    return r if r is not None else _real_urlopen(req, *args, **kwargs)


urllib.request.build_opener = _build_opener
urllib.request.urlopen = _urlopen


class CompletedProcess:
    def __init__(self, args, returncode, stdout, stderr):
        self.args, self.returncode, self.stdout, self.stderr = args, returncode, stdout, stderr

    def check_returncode(self):
        if self.returncode:
            raise CalledProcessError(self.returncode, self.args, self.stdout, self.stderr)


class CalledProcessError(Exception):
    def __init__(self, returncode, cmd, output=None, stderr=None):
        super().__init__(f"Command {cmd!r} returned non-zero exit status {returncode}.")
        self.returncode, self.cmd, self.output, self.stdout, self.stderr = returncode, cmd, output, output, stderr


class SubprocessError(Exception):
    pass


class TimeoutExpired(SubprocessError):
    pass


def _tool(argv, data):
    r = js.globasa_run_tool(argv[0], js.Array.from_(argv[1:]), data)
    return int(r.status), str(r.stdout), str(r.stderr)


def _run(args, input=None, capture_output=False, text=None, shell=False, check=False,
         encoding=None, errors=None, universal_newlines=None, stdout=None, stderr=None,
         timeout=None, env=None, cwd=None, **_):
    as_text = bool(text or encoding or universal_newlines)
    data = input if input is not None else ""
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    if shell or isinstance(args, str):
        cmds = [shlex.split(c) for c in str(args).split(" | ")]
    else:
        cmds = [[str(a) for a in args]]
    status, err_all = 0, []
    for argv in cmds:
        status, data, err = _tool(argv, data)
        if err:
            err_all.append(err)
        if status:
            break
    err_text = "\n".join(err_all)
    out = data if as_text else data.encode("utf-8")
    err_out = err_text if as_text else err_text.encode("utf-8")
    if not capture_output and stdout is None:
        sys.stdout.write(data)
        out = None
    if not capture_output and stderr is None:
        sys.stderr.write(err_text)
        err_out = None
    cp = CompletedProcess(args, status, out, err_out)
    if check:
        cp.check_returncode()
    return cp


shim = types.ModuleType("subprocess")
shim.run = _run
shim.CompletedProcess = CompletedProcess
shim.CalledProcessError = CalledProcessError
shim.SubprocessError = SubprocessError
shim.TimeoutExpired = TimeoutExpired
shim.PIPE, shim.STDOUT, shim.DEVNULL = -1, -2, -3
sys.modules["subprocess"] = shim


NEED_ANALYSIS = -1000


def run_step(path, args, stream, env):
    """Run one Python step; returns (status, stdout, stderr), or (NEED_ANALYSIS, url, text)
    when the step asked the browser NLP for an analysis it does not have yet."""
    code = _code.get(path)
    if code is None:
        with open(path, encoding="utf-8") as f:
            code = _code[path] = compile(f.read(), path, "exec")
    saved = (sys.argv, sys.stdin, sys.stdout, sys.stderr, dict(os.environ))
    sys.argv = [path] + list(args)
    sys.stdin = io.TextIOWrapper(io.BytesIO(stream.encode("utf-8")), encoding="utf-8")
    out, err = io.StringIO(), io.StringIO()
    sys.stdout, sys.stderr = out, err
    os.environ.update({str(k): str(v) for k, v in env.items()})
    status, need = 0, None
    try:
        exec(code, {"__name__": "__main__", "__file__": path, "__builtins__": builtins})
    except NeedAnalysis as e:
        need = (NEED_ANALYSIS, e.url, e.text)
    except SystemExit as e:
        if e.code not in (None, 0):
            status = e.code if isinstance(e.code, int) else 1
            if not isinstance(e.code, int):
                err.write(str(e.code) + "\n")
    except BaseException:
        import traceback
        traceback.print_exc(file=err)
        status = 1
    finally:
        sys.stdout.flush()
        sys.argv, sys.stdin, sys.stdout, sys.stderr = saved[:4]
        os.environ.clear()
        os.environ.update(saved[4])
    if need:
        return need
    return status, out.getvalue(), err.getvalue()
