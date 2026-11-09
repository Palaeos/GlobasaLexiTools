import pytest

from word_selection import pipeline, select


def test_pivot_support_from_provenance():
    w = {"provenance": ["wiktionary:de:Topf/noun", "wiktionary:en:pot/noun (headword)", "seed"]}
    assert pipeline.pivot_support(w) == ["de:Topf", "en:pot"]


def _c(lang_words, pivots):
    return {"members": [{"lang": l, "word": w, "pivot_support": pivots} for l, w in lang_words]}


def test_pivots_break_ties_only_after_methodology():
    a = _c([("ar", "x"), ("tr", "y")], ["en:pot"])
    b = _c([("ar", "x2"), ("tr", "y2")], ["en:pot", "de:Topf", "fr:cruche"])
    ranked = select.rank([a, b])
    assert ranked[0] is b and "backed by 3 of 3 pivots" in b["why"]
    assert "only through the English table" in a["why"]
    # more families still wins whatever the pivots say
    c = _c([("ar", "x3"), ("tr", "y3"), ("ko", "z3")], [])
    assert select.rank([a, b, c])[0] is c


def test_single_pivot_changes_nothing():
    a = _c([("ar", "x"), ("tr", "y")], ["en:pot"])
    b = _c([("ar", "x2"), ("tr", "y2"), ("fa", "z2")], [])
    ranked = select.rank([a, b])
    assert ranked[0] is b and ranked[0]["rank_key"][3] == 0 and "pivots" not in a["why"]


@pytest.mark.slow
def test_tuple_picks_shared_sense():
    from word_selection.sources import seeds
    rs = {tuple(r["seed"]): r for r in seeds.tuple_senses(
        seeds.parse("en:pot, ru:горшок, de:Topf, es:vasija, fr:cruche"))}
    topf = rs[("de", "Topf")]
    if not topf["built"]:
        pytest.skip("de edition not built")
    assert topf["senses"][topf["pick"]]["sense"] == "kleines Gefäß"
    assert not rs[("ru", "горшок")]["built"]
