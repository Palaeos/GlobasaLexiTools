from word_selection import pipeline


def _cluster():
    ko = {"lang": "ko", "word": "기질", "han": ["氣質", "器質", "基質"], "forms": ["gijil"]}
    vi = {"lang": "vi", "word": "khí chất", "han": ["氣質"], "forms": ["hi cet"]}
    ja = {"lang": "ja", "word": "気質", "han": ["氣質"], "forms": ["kixitsu"]}
    return {"members": [ja, ko, vi]}, ko, vi, ja


def test_shared_spelling_chosen():
    c, ko, vi, ja = _cluster()
    assert pipeline.display_han(ko, c) == "氣質"
    assert pipeline.han_unconfirmed(ko, c["members"]) == ["器質", "基質"]


def test_unconfirmed_homographs_not_shown():
    # native 독 'jar': the hanja table lists homographs 毒, 獨
    dok = {"lang": "ko", "word": "독", "han": ["毒", "獨"], "forms": ["dok"]}
    c = {"members": [dok, {"lang": "en", "word": "pot", "forms": ["pot"]}]}
    assert pipeline.display_han(dok, c) == ""
    assert pipeline.display_han(dok) == ""
    assert "毒" not in pipeline.lexiliasel(c)


def test_only_korean_and_vietnamese():
    c, ko, vi, ja = _cluster()
    assert pipeline.display_han(ja, c) == ""


def test_lexiliasel_format():
    c, *_ = _cluster()
    s = pipeline.lexiliasel(c)
    assert "Koreasa (기질 氣質 “gijil”)" in s
    assert "Vyetnamsa (khí chất 氣質 “hi cet”)" in s
