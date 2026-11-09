import pytest

from word_selection import pipeline, precedent

MATRIX = [{"lang": "cmn", "word": "基质", "form": "ji ji"},
          {"lang": "ja", "word": "基質", "form": "kixitsu"},
          {"lang": "ko", "word": "기질", "form": "gijil"}]


@pytest.mark.slow
def test_matrix_geology_prefers_kijitu():
    # 基質: k at cmn:j ja:k ko:g by precedent, Middle Chinese -t as -tu
    assert pipeline.propose(MATRIX, "b")[0]["form"] == "kijitu"


@pytest.mark.slow
def test_letter_fallback_needs_three_languages_and_evidence():
    assert precedent.lookup({"cmn": "j", "ja": "k", "ko": "g"})[0] == "k"
    assert precedent.lookup({"hi": "r", "te": "l"}, group="indic") is None or \
        "same letter" not in dict(precedent.lookup({"hi": "r", "te": "l"}, group="indic")[3])


@pytest.mark.slow
def test_t_coda_stats_count_only_blended_codas():
    cnt, ex, n = precedent.coda_stats()["t"]
    assert "pilpil" not in ex.get("", []) and cnt["tu"] / n >= 0.5
