"""Copy a tool's main() source with main renamed and an explicit "return 0;".

Only a function named main gets C++'s implicit "return 0" when control reaches its
closing brace. Renamed (-Dmain=x), that path is undefined behaviour and clang
compiles it to "unreachable", so apertium-pretransfer, apertium-tagger and cg-proc
trapped after writing correct output. The copy keeps every other line as it is.

    python3 rename_main.py SRC OUT NEW_NAME [--isolate]

--isolate (the flex-generated apertium-destxt / apertium-retxt): the whole file goes into
its own namespace, with a global NEW_NAME forwarding to it, because the two scanners
define the same non-static globals (buffer, escape, usage, ...). Every #include is also
copied above the namespace, so headers are first included at global scope and the
copies inside are no-ops (include guards).
"""
import re
import sys

src, out, name = sys.argv[1:4]
isolate = "--isolate" in sys.argv[4:]
text = open(src, encoding="utf-8").read()
m = re.search(r"\bint\s+main\s*\(", text)
if not m:
    sys.exit(f"{src}: no int main(")
i = text.index(")", m.end())
open_brace = text.index("{", i)
depth, k, n = 0, open_brace, len(text)
while k < n:
    c = text[k]
    if text.startswith("//", k):
        k = text.find("\n", k)
        k = n if k < 0 else k
        continue
    if text.startswith("/*", k):
        k = text.index("*/", k) + 2
        continue
    if c in "\"'":
        if c == '"' and text[k - 1] == "R":      # raw string R"d(...)d"
            delim = text[k + 1:text.index("(", k)]
            k = text.index(")" + delim + '"', k) + len(delim) + 2
            continue
        k += 1
        while text[k] != c:
            k += 2 if text[k] == "\\" else 1
        k += 1
        continue
    if c == "{":
        depth += 1
    elif c == "}":
        depth -= 1
        if depth == 0:
            break
    k += 1
else:
    sys.exit(f"{src}: unbalanced braces in main")
body = text[:m.start()] + f"int {name}(" + text[m.end():k] + "\n  return 0;\n" + text[k:]
if isolate:
    includes = []
    for line in text.splitlines():
        if re.match(r"\s*#\s*include\b", line) and line.strip() not in includes:
            includes.append(line.strip())
    ns = f"{name}_isolated"
    body = ("\n".join(includes) + f"\nnamespace {ns} {{\n" + body +
            f"\n}}  // namespace {ns}\nint {name}(int argc, char** argv) {{ return {ns}::{name}(argc, argv); }}\n")
with open(out, "w", encoding="utf-8") as f:
    f.write(body)
