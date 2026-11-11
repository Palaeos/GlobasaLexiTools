"""CLI entry point: check Globasa text from stdin or arguments."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GlobasaGrammarChecker.checker import GrammarChecker

checker = GrammarChecker()

if len(sys.argv) > 1:
    text = " ".join(sys.argv[1:])
else:
    text = sys.stdin.read()

matches = checker.check_text(text)
if not matches:
    print("No grammar issues found.")
else:
    for m in matches:
        print(f"[{m.rule_id}] offset {m.offset}: {m.message}")
        if m.suggestions:
            print(f"  Suggestion: {m.suggestions[0]}")
