"""merge_gold_priors.py — Merge manually-annotated gold alignments into eflomal priors.

Called from run_giza_improved.py _build_eflomal_priors() after all existing
prior writes. Reads gold_alignments/{lang}.tsv, derives LEX/HMMF/HMMR/FERF/FERR
priors via eflomal.calculate_priors(), and appends them to the priors file with a
high alpha multiplier so gold evidence dominates dictionary priors.

TSV columns (tab-separated):
    sentence_id  glb_tokens  tgt_tokens  links_json  annotator  iso_timestamp  tier

Only records whose latest tier is "gold" feed into priors — quality over
quantity. Auto-saved edits in the annotator UI write tier="saved" and are
ignored here until the user explicitly confirms them via the
"Confirm as gold" button. Legacy 6-column rows default to tier="saved"
(must be reconfirmed before influencing priors).

Multiple records per sentence_id are allowed; only the latest (by timestamp) is used.
"""

import json
import os
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLD_DIR = os.path.join(BASE_DIR, "gold_alignments")

GOLD_ALPHA_MULTIPLIER = 5.0


def _pharaoh(links, n_src=None, n_tgt=None):
    """Convert [[i,j], ...] list to Pharaoh-format string 'i-j i-j ...'

    Skips NULL links (i == -1 or j == -1) since eflomal calculates NULLs
    internally; including them would corrupt the index range checks.

    When n_src/n_tgt are given, also drops links that point past the end of
    either token list. Such links exist in older gold records that were saved
    against a different sentence (see the sentence_id corruption noted in
    cerebrum). eflomal.calculate_priors raises on the first out-of-bounds
    link — and its error path is itself buggy (`'...%d' % lineno + 1` raises
    TypeError instead of ValueError) — so a single bad record would otherwise
    discard every gold prior.
    """
    parts = []
    dropped = 0
    for pair in links:
        i, j = pair[0], pair[1]
        if i < 0 or j < 0:
            continue
        if (n_src is not None and i >= n_src) or (n_tgt is not None and j >= n_tgt):
            dropped += 1
            continue
        parts.append(f"{i}-{j}")
    return " ".join(parts), dropped


def _load_gold(lang):
    """Load latest gold annotation per sentence_id from gold_alignments/{lang}.tsv.

    Returns list of dicts: [{sentence_id, glb_tokens, tgt_tokens, links}]
    sorted by sentence_id.
    """
    tsv_path = os.path.join(GOLD_DIR, f"{lang}.tsv")
    if not os.path.isfile(tsv_path):
        return []

    latest = {}  # sentence_id -> (timestamp, record)
    with open(tsv_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 6:
                continue
            try:
                sid = int(parts[0])
                glb_tokens = parts[1]
                tgt_tokens = parts[2]
                links = json.loads(parts[3])
                annotator = parts[4]  # noqa: F841
                timestamp = parts[5]
                tier = parts[6] if len(parts) >= 7 else "saved"
            except (ValueError, json.JSONDecodeError):
                continue

            if sid not in latest or timestamp > latest[sid][0]:
                latest[sid] = (timestamp, {
                    "sentence_id": sid,
                    "glb_tokens": glb_tokens,
                    "tgt_tokens": tgt_tokens,
                    "links": links,
                    "tier": tier,
                })

    # Filter out tombstones (links is null) AND non-gold records.
    # Only "gold" rows feed priors — auto-saved edits are work-in-progress
    # that the user hasn't yet confirmed.
    return [v for _, v in sorted(latest.values(), key=lambda x: x[1]["sentence_id"])
            if v["links"] is not None and v["tier"] == "gold"]


def append_gold_priors(lang, priors_file):
    """Append gold-derived priors to an existing priors file.

    Args:
        lang:         Target language code (e.g. "en").
        priors_file:  Path to the eflomal priors file (opened for appending).

    Returns the number of gold sentences processed (0 if no gold data).
    """
    records = _load_gold(lang)
    if not records:
        return 0

    src_sentences = [r["glb_tokens"] for r in records]
    tgt_sentences = [r["tgt_tokens"] for r in records]
    fwd_alignments = []
    n_dropped = 0
    n_records_affected = 0
    for r, src, tgt in zip(records, src_sentences, tgt_sentences):
        pharaoh, dropped = _pharaoh(r["links"],
                                    len(src.strip().split()),
                                    len(tgt.strip().split()))
        if dropped:
            n_dropped += dropped
            n_records_affected += 1
            print(f"  [gold priors] {lang}: dropped {dropped} out-of-bounds "
                  f"link(s) in sentence_id {r['sentence_id']}", file=sys.stderr)
        fwd_alignments.append(pharaoh)
    if n_dropped:
        print(f"  [gold priors] {lang}: {n_dropped} out-of-bounds link(s) "
              f"across {n_records_affected} record(s) — these gold rows are "
              f"stale and should be re-annotated", file=sys.stderr)
    rev_alignments = fwd_alignments  # gold links are symmetric

    # Filter out any sentence where the pharaoh string is empty
    # (annotation with only NULL links — skip rather than crash)
    valid = [
        (s, t, f, rv)
        for s, t, f, rv in zip(src_sentences, tgt_sentences, fwd_alignments, rev_alignments)
        if f.strip()
    ]
    if not valid:
        return 0

    src_sentences, tgt_sentences, fwd_alignments, rev_alignments = zip(*valid)

    try:
        import eflomal
        priors, hmmf, hmmr, ferf, ferr = eflomal.calculate_priors(
            list(src_sentences),
            list(tgt_sentences),
            list(fwd_alignments),
            list(rev_alignments),
        )
    except Exception as e:
        print(f"  [gold priors] eflomal.calculate_priors failed for {lang}: {e}",
              file=sys.stderr)
        return 0

    m = GOLD_ALPHA_MULTIPLIER
    with open(priors_file, "a", encoding="utf-8") as f:
        for (src, tgt), alpha in sorted(priors.items()):
            f.write(f"LEX\t{src}\t{tgt}\t{alpha * m:.4f}\n")
        for (src, fert), alpha in sorted(ferf.items()):
            f.write(f"FERF\t{src}\t{fert}\t{alpha * m:.4f}\n")
        for (tgt, fert), alpha in sorted(ferr.items()):
            f.write(f"FERR\t{tgt}\t{fert}\t{alpha * m:.4f}\n")
        for jump, alpha in sorted(hmmf.items()):
            f.write(f"HMMF\t{jump}\t{alpha * m:.4f}\n")
        for jump, alpha in sorted(hmmr.items()):
            f.write(f"HMMR\t{jump}\t{alpha * m:.4f}\n")

    n = len(valid)
    print(f"  [gold priors] Appended priors from {n} gold sentences for glb-{lang}")
    return n
