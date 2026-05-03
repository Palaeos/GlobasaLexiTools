"""
Syllable fallback — Tier 2 of the cascade.

Thin wrapper over Hyphenation.hyphenation (the project's existing Hyphenation.py).
Imports only the `hyphenation` function; avoids Hyphenation.py's import-time side effects
(file I/O, wget calls) by importing the function directly.

The hyphenation() function returns a hyphenated string (e.g. "ki-ta-bu").
We split on '-' to get syllables, then build (start, end, surface) tuples.
"""

from __future__ import annotations

import sys
import os

_PROJ_ROOT = os.path.dirname(os.path.dirname(__file__))


def _get_hyphenation_fn():
    """Import the hyphenation function from Hyphenation.py without running its side effects."""
    import importlib.util
    path = os.path.join(_PROJ_ROOT, "Hyphenation.py")
    if not os.path.exists(path):
        return None
    # Temporarily redirect stdout to suppress any print() in the module
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        spec = importlib.util.spec_from_file_location("_hyphenation_module", path)
        mod = importlib.util.module_from_spec(spec)
        # We need to neutralise the file I/O at module level.
        # Hyphenation.py does I/O at module top level AFTER defining hyphenation().
        # We'll extract just the function definition by exec'ing only the function.
        with open(path, encoding="utf-8") as f:
            source = f.read()
        # Parse: execute only the parts before "menalari_name = ..."
        # (everything after that is the script-level word-list processing)
        cutoff_markers = [
            "menalari_name =",
            "hyphenations = set()",
            "with open(",
        ]
        lines = source.splitlines()
        safe_lines = []
        stop = False
        for line in lines:
            if not stop:
                for marker in cutoff_markers:
                    if line.strip().startswith(marker):
                        stop = True
                        break
            if not stop:
                safe_lines.append(line)
        safe_source = "\n".join(safe_lines)
        ns = {}
        exec(compile(safe_source, path, "exec"), ns)
        return ns.get("hyphenation")
    except Exception:
        return None
    finally:
        sys.stdout = old_stdout


_hyphenation_fn = None


def _ensure_loaded() -> None:
    global _hyphenation_fn
    if _hyphenation_fn is None:
        _hyphenation_fn = _get_hyphenation_fn()


def syllabify(word: str) -> list[str]:
    """Return list of syllable strings for word. Falls back to bigrams if unavailable."""
    _ensure_loaded()
    if _hyphenation_fn is None:
        # Fallback: split into bigrams
        return [word[i:i+2] for i in range(0, len(word), 2)]
    try:
        result = _hyphenation_fn(word.lower())
        if isinstance(result, str) and result:
            syllables = result.split("-")
            # Restore original case per syllable
            out = []
            pos = 0
            for syl in syllables:
                out.append(word[pos: pos + len(syl)])
                pos += len(syl)
            return out if out else [word]
        return [word]
    except Exception:
        return [word]


def syllable_cover(word: str) -> list[tuple[int, int, str]]:
    """Return (start, end, surface) tuples for syllable split of word."""
    syllables = syllabify(word)
    out = []
    pos = 0
    for syl in syllables:
        out.append((pos, pos + len(syl), syl))
        pos += len(syl)
    return out
