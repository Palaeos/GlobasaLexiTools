# Word-level variants between The War of the Worlds as first published in book form (Heinemann
# 1898) and as Wells revised it for the Atlantic Edition (1924), both public domain. Where Wells
# reworded a passage, the other reading often shows the plainer wording a paraphrase can follow
# (user, 2026-11-20: use the editions to inform paraphrases). Method: edition_variants.py.
#
# Output: atlantic_variants.tsv (h_sentence_no, ratio, kind, heinemann, atlantic, h_context);
#         lexical_variants.tsv: the short word changes only (edition_variants.lexical), with
#         context, for the paraphrase work.
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from edition_variants import lexical, sentences, variants, write_tsv

HERE = Path(__file__).parent

H = sentences(HERE / "text" / "heinemann.txt")
A = sentences(HERE / "text" / "atlantic.txt")
found = variants(H, A)
write_tsv(HERE / "atlantic_variants.tsv", H, found, "heinemann", "atlantic", prefix="h")
write_tsv(HERE / "lexical_variants.tsv", H, [v for v in found if lexical(v)], "heinemann", "atlantic", prefix="h")
print(len(H), "Heinemann sentences,", len(A), "Atlantic;", len(found), "variants:", dict(Counter(v[2] for v in found)))
print(sum(1 for v in found if lexical(v)), "short word changes in lexical_variants.tsv")
