from word_selection import pipeline


def _cluster():
    ko = {"lang": "ko", "word": "기질", "han": ["氣質", "器質", "基質"], "forms": ["gijil"]}
    vi = {"lang": "vi", "word": "khí chất", "han": ["氣質"], "forms": ["hi cet"]}
    ja = {"lang": "ja", "word": "気質", "han": ["氣質"], "forms": ["kixitsu"]}
    return {"members": [ja, ko, vi]}, ko, vi, ja


def test_shared_spelling_chosen():
    c, ko, vi, ja = _cluster()
    assert pipeline.display_han(ko, c) == "氣質"
    assert pipeline.display_han(ko) == "氣質 / 器質 / 基質"


def test_only_korean_and_vietnamese():
    c, ko, vi, ja = _cluster()
    assert pipeline.display_han(ja, c) == ""
    assert pipeline.display_han({"lang": "ko", "word": "아카데미", "han": []}) == ""


def test_lexiliasel_format():
    c, *_ = _cluster()
    s = pipeline.lexiliasel(c)
    assert "Koreasa (기질 氣質 “gijil”)" in s
    assert "Vyetnamsa (khí chất 氣質 “hi cet”)" in s
