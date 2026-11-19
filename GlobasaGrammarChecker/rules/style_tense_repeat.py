from .base import GrammarRule, GrammarMatch

# Tense/mood particles (xwexi 03.gramati/07.falelexili-morfo). Compound tenses (le le, xa le, ...)
# are compared as whole sequences, so "le le V ji le V" is a tense change and is not flagged.
# am is left out: each command is its own utterance, and a repeated am is rhetorical
# ("Am jagegi te, am yonfobi te, am fobi te!").
TENSE_PARTICLES = {"le", "xa", "nun", "ger", "jale", "jaxa"}
COORDINATORS = {"ji", "mas", "or"}
# Words that open a subordinate clause: after one, a comma may close that clause and the next
# particle belong to the main clause ("Un te, hu da le firaru, le morcu.").
SUBORDINATORS = {"hu", "ki", "eger", "koski", "durki", "celki", "kom", "denwatu", "finki",
                 "xafeki", "lefeki", "hataki", "kos"}
# Words that may stand between the particle and its verb (no, adverbs)
TRANSPARENT = {"no", "daymo", "haji", "uje", "fori", "pimpan", "nadir", "hata", "pia", "sol",
               "kriban", "godomo", "lilmo", "kufi", "du"}


class RepeatedTenseRule(GrammarRule):
    """Suggestion: a tense/mood particle repeated on a coordinated verb of the same predicate.

    Xwexi (03.gramati/07, Omission of Verb Particles): "the particle for any tense/mood may be
    omitted in subsequent verbs within a clause once the tense/mood has been established with
    the first verb of each predicate." English marks past on every verb; Globasa need not:

    TRANSLATIONESE: Mi le resta totalmo harkakal ji le loga nilto.
    NATURAL:        Mi le resta totalmo harkakal ji loga nilto.

    Fires only when the repeated particle directly follows ji/mas/or, or a comma in a
    sentence with no subordinate clause before it (so no new subject phrase intervenes,
    which would establish the tense anew), and the nearest earlier particle sequence in the
    sentence is the same. am (imperative) is excluded. A style hint, never an error: repeating
    the particle is grammatical, and a writer may want it for emphasis.
    """
    rule_id = "GLOBASA_STYLE_REPEATED_TENSE"

    def check(self, tokens, pos_list, lemmas, text):
        n = len(tokens)
        # character offset of every token, found left to right
        offsets, cursor = [], 0
        for surface, _, _ in tokens:
            i = text.find(surface, cursor)
            offsets.append(i if i >= 0 else cursor)
            cursor = (i if i >= 0 else cursor) + len(surface)

        def particle_run(i):
            """(particles, index of the word after them) if a tense-particle run starting at i
            governs a verb, else None."""
            j, run = i, []
            while j < n and pos_list[j] == "PAR" and lemmas[j] in TENSE_PARTICLES:
                run.append(lemmas[j])
                j += 1
            if not run:
                return None
            k = j
            while k < n and lemmas[k] in TRANSPARENT:
                k += 1
            return (tuple(run), j) if k < n and pos_list[k] == "V" else None

        matches, previous, prev_end, i = [], None, 0, 0
        while i < n:
            found = particle_run(i)
            if not found:
                i += 1
                continue
            run, after = found
            before = i - 1
            # comma case: only in a sentence with no subordinate clause so far, since the comma
            # may close one ("Denwatu hu satu le rinjon, le hay toka")
            # (PosTagger joins phrases such as 'denwatu hu' into one token: test each word)
            between = {w for lem in lemmas[:i] if lem for w in lem.split()}
            joined = before >= 0 and (lemmas[before] in COORDINATORS
                                      or (tokens[before][0].endswith(",")
                                          and not between & SUBORDINATORS))
            if previous == run and joined:
                start = offsets[i]
                end = offsets[after] if after < n else offsets[after - 1] + len(tokens[after - 1][0])
                span = text[start:end]
                shown = " ".join(run)
                matches.append(GrammarMatch(
                    rule_id=self.rule_id,
                    message=(f"Suggestion: '{shown}' is already set for this predicate; Globasa "
                             "may leave it out on the following verbs (xwexi, Omission of Verb "
                             "Particles). Repeating it on every verb mirrors English."),
                    offset=start,
                    length=len(span),
                    context=text[offsets[before]:end] if before >= 0 else span,
                    suggestions=[""],
                    issue_type="style",
                ))
            previous, prev_end = run, after
            i = after
        return matches
