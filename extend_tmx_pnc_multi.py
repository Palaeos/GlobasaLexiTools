"""
Extend Doxo_passages.tmx with Pepper & Carrot translations from transcript files.
Uses markdown transcript files from the peppercarrot/webcomics repo.
Aligns by sequential English text matching, then lookups by (page, within_page_index).
"""

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from glob import glob

TMX_FILE = "Doxo_passages.tmx"
PNC_DIR = Path("/tmp/peppercarrot_repo")

# Episode directory names → TMX context strings
EPISODES = {}
for ep_dir in sorted(PNC_DIR.glob("ep[0-9][0-9]_*")):
    ep_num = int(ep_dir.name[2:4])
    if 1 <= ep_num <= 12:
        EPISODES[ep_num] = {
            "dir": ep_dir,
            "context": f"Pilpil ji Karote: Mon {ep_num}",
        }

# Target languages to add (will check transcript availability per episode)
# P&C uses some non-standard codes: cn=zh, kr=ko
TARGET_LANGS = ["de", "fr", "eo", "ru", "pt", "id", "da", "nl",
                "pl", "vi", "hu", "uk",
                "cn", "ja", "kr", "he"]

# Map P&C lang codes to TMX lang codes where they differ
PNC_TO_TMX_LANG = {"cn": "zh", "kr": "ko"}



def parse_transcript(path):
    """Parse a P&C transcript markdown file.
    Returns flat ordered list of (page, within_page_idx, name, text).
    """
    entries = []
    page_counts = {}  # page → running index
    with open(path, encoding="utf-8") as f:
        current_page = None
        in_table = False
        for line in f:
            line = line.strip()
            m = re.match(r"### (P\d+)", line)
            if m:
                current_page = m.group(1)
                in_table = False
                page_counts.setdefault(current_page, 0)
                continue
            if line.startswith("----"):
                in_table = True
                continue
            if in_table and "|" in line and current_page:
                parts = line.split("|")
                if len(parts) >= 4:
                    name = parts[0].strip()
                    text = parts[3].strip()
                    idx = page_counts[current_page]
                    entries.append((current_page, idx, name, text))
                    page_counts[current_page] += 1
    return entries


def find_transcript(ep_dir, lang):
    """Find transcript file for a language in an episode directory."""
    ep_num = ep_dir.name[2:4]
    path = ep_dir / "lang" / lang / f"ep{ep_num}_{lang}_transcript.md"
    if path.exists():
        return path
    # Try glob fallback
    matches = list((ep_dir / "lang" / lang).glob("*transcript.md"))
    return matches[0] if matches else None


# --- Parse TMX ---
tree = ET.parse(TMX_FILE)
root = tree.getroot()
body = root.find("body")

total_added = 0

for ep_num, ep_info in sorted(EPISODES.items()):
    context = ep_info["context"]
    ep_dir = ep_info["dir"]

    # Find English transcript
    en_transcript = find_transcript(ep_dir, "en")
    if not en_transcript:
        print(f"SKIP ep{ep_num:02d}: no English transcript")
        continue

    en_entries = parse_transcript(en_transcript)

    # Collect TMX TUs for this episode
    ep_tus = []
    for tu in body.findall("tu"):
        prop = tu.find("prop")
        if prop is not None and prop.text == context:
            # Get English text
            for tuv in tu.findall("tuv"):
                if tuv.get("{http://www.w3.org/XML/1998/namespace}lang") == "en":
                    ep_tus.append((tu, tuv.find("seg").text))
                    break

    if not ep_tus:
        print(f"SKIP ep{ep_num:02d}: no TMX entries for '{context}'")
        continue

    # Sequential match: TMX English → English transcript → (page, idx) keys
    en_idx = 0
    tmx_keys = []  # (page, within_page_idx) for each TMX TU
    for tu, tmx_text in ep_tus:
        found = False
        while en_idx < len(en_entries):
            if en_entries[en_idx][3] == tmx_text:
                tmx_keys.append((en_entries[en_idx][0], en_entries[en_idx][1]))
                en_idx += 1
                found = True
                break
            en_idx += 1
        if not found:
            tmx_keys.append(None)

    matched_keys = sum(1 for k in tmx_keys if k is not None)
    if matched_keys < len(ep_tus):
        print(f"  ep{ep_num:02d}: matched {matched_keys}/{len(ep_tus)} TMX→transcript")

    # Process each target language
    ep_added = {}
    for lang in TARGET_LANGS:
        lang_transcript = find_transcript(ep_dir, lang)
        if not lang_transcript:
            continue

        lang_entries = parse_transcript(lang_transcript)
        # Build (page, idx) → text lookup
        lang_lookup = {(page, idx): text for page, idx, name, text in lang_entries}

        # Map P&C lang code to TMX lang code
        tmx_lang = PNC_TO_TMX_LANG.get(lang, lang)

        added = 0
        for i, (tu, tmx_text) in enumerate(ep_tus):
            key = tmx_keys[i]
            if key is None:
                continue

            # Check if language already present (using TMX lang code)
            existing = False
            for tuv in tu.findall("tuv"):
                if tuv.get("{http://www.w3.org/XML/1998/namespace}lang") == tmx_lang:
                    existing = True
                    break
            if existing:
                continue

            lang_text = lang_lookup.get(key, "")
            if lang_text:
                tuv = ET.SubElement(tu, "tuv")
                tuv.set("xml:lang", tmx_lang)
                seg = ET.SubElement(tuv, "seg")
                seg.text = lang_text
                added += 1

        if added:
            ep_added[lang] = added
            total_added += added

    if ep_added:
        summary = ", ".join(f"{l}={c}" for l, c in sorted(ep_added.items()))
        print(f"  ep{ep_num:02d} ({len(ep_tus)} TUs): {summary}")

# Write output to separate file to preserve original TMX
OUT_FILE = TMX_FILE.replace(".tmx", "_extended.tmx") if isinstance(TMX_FILE, str) else "Doxo_passages_extended.tmx"
tree_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
pretty = minidom.parseString(tree_str).toprettyxml(indent="  ", encoding="UTF-8")

with open(OUT_FILE, "wb") as f:
    f.write(pretty)

print(f"\nAdded {total_added} TUVs total. Wrote {len(body.findall('tu'))} TUs to {OUT_FILE}")
print(f"Original {TMX_FILE} is untouched. Verify and rename manually.")
