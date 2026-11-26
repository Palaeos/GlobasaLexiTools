"""Optional Rust extension rust/globasa_fast (built by ./setup.sh --fast).

    from fast_ext import fast      # the globasa_fast module, or None

Without it every caller runs its pure-Python original, which stays the reference: same results,
only slower. GLOBASA_FAST=0 forces the Python path (to test it, or to compare).
"""
import os
import sys

fast = None
if os.environ.get("GLOBASA_FAST") == "0":
    _why = "GLOBASA_FAST=0"
else:
    try:
        import globasa_fast as fast
    except ImportError:
        _why = "globasa_fast not built; ./setup.sh --fast builds it"
if fast is None:
    print(f"(fallback: {_why}) pure-Python alignment/diff/annealing routines, slower",
          file=sys.stderr)
