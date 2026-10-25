"""Propose cut points and names for Hector's lesson word-list recordings, as
Audacity label tracks, so later lessons can be split the way lessons 1-7 were
by hand.

Each darsu_NN_lexilista.mp3 reads the lesson's word list in one take, but not
always all of it (lesson 5 reads 21 of its 28 entries) and not always one
segment per entry. Cuts come from ffmpeg's silencedetect, padded by PAD on both
sides (the margin the hand-cut clips leave; checked against lessons 1, 3, 4, 6
and 7, where the segments pair one-to-one with the clips).

Names come from what is actually said. A phoneme recogniser (wav2vec2 trained
to output IPA, MODEL_DIR) transcribes each segment; Globasa spelling is fully
phonemic, so the IPA maps straight back to letters (IPA_TO_LETTER) and is
compared with each list word by edit distance. An in-order alignment then pairs
segments with words, allowing words the recording never reads, segments no
word explains, and a phrase spoken in two segments. A label whose phonemes sit
further than SURE from its word ends in "?": listen before exporting.

Labels use underscores for spaces, as Ektor_su_Lafuzu_processed names its
files. Import a track in Audacity (File > Import > Labels) on the lesson's mp3,
check it, then File > Export > Export Multiple, split by labels, named by label
text -- or review them in the Word Viewer at /splits, which plays each
segment, takes corrections and exports checked clips. Its state lives in a
.json beside each track; a lesson with one is never regenerated. Lessons
already cut by hand are skipped.
"""
import glob
import json
import os
import re
import subprocess

import numpy as np
import pandas as pd
import torch
from transformers import (Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC,
                          Wav2Vec2PhonemeCTCTokenizer)

from xwexi_lessons import LESSONS_DIR, clip_name, lesson_entries, spoken_forms

CLIPS_DIR = "/media/paleos/Warehouse2/Applications/Segmentation/Ektor_su_Lafuzu_processed"
MODEL_DIR = "Models/wav2vec2-lv-60-espeak-cv-ft"
OUT_DIR = "LessonAudioLabels"
NOISE_DB, MIN_SILENCE, MIN_SPEECH = -40, 0.35, 0.15
PAD = 0.12
RATE, FRAME = 16000, 0.02          # wav2vec2: one output frame per 20 ms
# Alignment costs, on the same scale as a word's normalised edit distance: a
# list word the recording never reads, a segment no word explains, and the
# extra for a phrase spoken in two segments.
SKIP_WORD, SKIP_SEGMENT, MERGE = 0.7, 0.9, 0.1
SURE = 0.35

# Recogniser IPA -> Globasa letter. The spelling is fully phonemic (xwexi,
# Alphabet and Pronunciation): c = t͡ʃ, j = d͡ʒ, x = ʃ, h = x, y = j, r = ɾ.
# Allophones and near misses the model reports for Hector's speech fold onto
# the same letter (a trilled r, aspiration, length); schwa has no letter.
IPA_TO_LETTER = {
    "tʃ": "c", "t͡ʃ": "c", "tɕ": "c", "dʒ": "j", "d͡ʒ": "j", "dʑ": "j",
    "ʃ": "x", "ɕ": "x", "ʂ": "x", "x": "h", "χ": "h", "h": "h", "ħ": "h",
    "j": "y", "ɾ": "r", "r": "r", "ɹ": "r", "ɻ": "r", "ʁ": "r",
    "ɛ": "e", "ɔ": "o", "ɪ": "i", "ʊ": "u", "ɐ": "a", "ɑ": "a", "æ": "a",
    "ŋ": "n", "ɡ": "g", "ʒ": "z", "β": "v", "ʋ": "v", "ɸ": "f",
}
# Substitutions that cost half: sounds Hector's recordings blur.
NEAR = {frozenset(p) for p in ("uw", "iy", "ou", "ei", "sx", "cx", "bv")}


def letters(word):
    return re.sub(r"[^a-z]", "", word.lower())


def decode_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1",
                          "-ar", str(RATE), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def speech_segments(path):
    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", path, "-af",
         f"silencedetect=noise={NOISE_DB}dB:d={MIN_SILENCE}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", log).groups()
    total = int(h) * 3600 + int(m) * 60 + float(s)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    segs, t = [], 0.0
    for s0, e0 in zip(starts, ends + [total]):
        if s0 - t > MIN_SPEECH:
            segs.append((t, s0))
        t = e0
    if total - t > MIN_SPEECH:
        segs.append((t, total))
    return segs, total


class Recogniser:
    def __init__(self):
        self.features = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_DIR)
        self.tokens = Wav2Vec2PhonemeCTCTokenizer.from_pretrained(
            MODEL_DIR, do_phonemize=False)
        self.model = Wav2Vec2ForCTC.from_pretrained(MODEL_DIR).eval()
        self.blank = self.tokens.pad_token_id

    def frames(self, audio):
        """Best token id per 20 ms frame of the whole recording, so every
        segment is heard with its natural context."""
        with torch.no_grad():
            logits = self.model(**self.features(
                audio, sampling_rate=RATE, return_tensors="pt")).logits[0]
        return logits.argmax(-1).tolist()

    def spoken(self, ids, start, end):
        """Globasa letters heard between start and end (seconds)."""
        out, prev = [], None
        for i in ids[int(start / FRAME):int(end / FRAME) + 1]:
            if i != prev and i != self.blank:
                ipa = self.tokens.convert_ids_to_tokens(i).replace("ː", "").replace("ʰ", "")
                out.append(IPA_TO_LETTER.get(ipa, ipa))
            prev = i
        return "".join(o for o in out if o in "abcdefghijklmnoprstuvwxyz")


def distance(heard, word):
    """(distance, spoken form): the closest of the entry's spoken forms, by
    edit distance with NEAR pairs at half cost, normalised by its length."""
    return min((_distance(heard, f), f) for f in spoken_forms(word))


def _distance(heard, word):
    w = letters(word)
    prev = [float(j) for j in range(len(w) + 1)]
    for i, a in enumerate(heard, 1):
        cur = [float(i)]
        for j, b in enumerate(w, 1):
            sub = 0.0 if a == b else 0.5 if frozenset((a, b)) in NEAR else 1.0
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + sub))
        prev = cur
    return prev[-1] / max(len(w), 1)


def align(heard, words):
    """In-order pairing of segments with words. heard[i] is segment i's
    letters, heard2[i] those of segments i and i+1 together. Returns
    [(first segment, last segment, word or None, distance)] and skipped words."""
    S, W = len(heard), len(words)
    INF = float("inf")
    cost = [[INF] * (W + 1) for _ in range(S + 1)]
    back = [[None] * (W + 1) for _ in range(S + 1)]
    cost[0][0] = 0.0
    for i in range(S + 1):
        for j in range(W + 1):
            c = cost[i][j]
            if c == INF:
                continue
            moves = []
            if i < S and j < W:
                moves.append((i + 1, j + 1, distance(heard[i], words[j])[0], "one"))
            if i + 1 < S and j < W:
                moves.append((i + 2, j + 1, distance(heard[i] + heard[i + 1], words[j])[0]
                              + MERGE, "two"))
            if j < W:
                moves.append((i, j + 1, SKIP_WORD, "skipword"))
            if i < S:
                moves.append((i + 1, j, SKIP_SEGMENT, "skipseg"))
            for ni, nj, step, kind in moves:
                if c + step < cost[ni][nj]:
                    cost[ni][nj] = c + step
                    back[ni][nj] = (i, j, kind, step)
    out, skipped, i, j = [], [], S, W
    while (i, j) != (0, 0):
        pi, pj, kind, step = back[i][j]
        if kind == "one":
            out.append((pi, pi, words[pj], step))
        elif kind == "two":
            out.append((pi, pi + 1, words[pj], step - MERGE))
        elif kind == "skipword":
            skipped.append(words[pj])
        else:
            out.append((pi, pi, None, None))
        i, j = pi, pj
    return out[::-1], skipped[::-1]


def lexicon_words():
    """Every headword, for segments the lesson's list does not explain: Hector
    also reads forms from the lesson text ((fe) ban mara in lesson 18)."""
    df = pd.read_csv("word-list.csv", index_col=0, dtype=str)
    return sorted({str(w).strip() for w in df.index if str(w).strip()})


def propose(n, recogniser, lexicon):
    """Labels [(start, end, name, heard, distance, off the list?)] and
    skipped entries."""
    path = glob.glob(f"{LESSONS_DIR}/{n:02d}/*lexilista*.mp3")[0]
    segs, total = speech_segments(path)
    ids = recogniser.frames(decode_audio(path))
    heard = [recogniser.spoken(ids, s, e) for s, e in segs]
    pairs, skipped = align(heard, [w for w, _ in lesson_entries(n)])
    labels = []
    for k, (a, b, word, d) in enumerate(pairs):
        s, e = segs[a][0], segs[b][1]
        said = "".join(heard[a:b + 1])
        if word is None:
            # Not on the list: the closest headword of similar length, if any
            # is close enough to name it; otherwise leave it for the ear.
            near = [w for w in lexicon if abs(len(letters(w)) - len(said)) <= 2]
            d, form = min((distance(said, w) for w in near), default=(9.0, ""))
            name = (clip_name(form) if d <= SURE else f"unknown_{k + 1:02d}") + "?"
        else:
            d, form = distance(said, word)
            name = clip_name(form) + ("" if d <= SURE else "?")
        labels.append((max(0.0, s - PAD), min(total, e + PAD), name, said, d,
                       word is None))
    return labels, skipped


if __name__ == "__main__" or True:
    os.makedirs(OUT_DIR, exist_ok=True)
    done = {f[:-4] for f in os.listdir(CLIPS_DIR)} if os.path.isdir(CLIPS_DIR) else set()
    recogniser = Recogniser()
    lexicon = lexicon_words()
    for n in range(1, 21):
        words = [w for w, _ in lesson_entries(n)]
        if words and all(clip_name(spoken_forms(w)[-1]) in done for w in words[:3]):
            continue   # cut by hand already
        out = f"{OUT_DIR}/darsu_{n:02d}_lexilista.txt"
        review = out[:-4] + ".json"
        if os.path.exists(review):
            # The Word Viewer's /splits page keeps its work here; never
            # overwrite it. Delete both files to start the lesson afresh.
            print(f"lesson {n:2d}: in review ({review}), left alone")
            continue
        labels, skipped = propose(n, recogniser, lexicon)
        with open(out, "w", encoding="utf-8") as f:
            for s, e, name, *_ in labels:
                f.write(f"{s:.3f}\t{e:.3f}\t{name}\n")
        with open(review, "w", encoding="utf-8") as f:
            json.dump({"lesson": n, "not_heard": skipped,
                       "rows": [{"start": round(s, 3), "end": round(e, 3),
                                 "name": name, "heard": h,
                                 "distance": None if d is None else round(d, 3),
                                 "off_list": off, "checked": False}
                                for s, e, name, h, d, off in labels]},
                      f, ensure_ascii=False, indent=1)
        unsure = [f"{name} (heard {h!r}{', not on the list' if off else ''})"
                  for _, _, name, h, _, off in labels if name.endswith("?")]
        print(f"lesson {n:2d}: {len(labels):2d} labels for {len(words):2d} words, "
              f"{len(unsure)} to check -> {out}")
        if unsure:
            print(f"           check: {', '.join(unsure)}")
        if skipped:
            print(f"           not heard in the recording: {', '.join(skipped)}")
