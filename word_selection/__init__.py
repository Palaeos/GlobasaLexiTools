"""Word Selector: automated Globasa word selection.

Pipeline (each stage a plain function over dicts/lists):
    concept -> sources (gather) -> translit -> cluster -> select -> blend
            -> form_rules -> collision -> ranked proposals + dossier

Implements "Methodology for Lexical Development" (repo root), with one update:
Filipino is no longer a source language (16 sources).
"""
