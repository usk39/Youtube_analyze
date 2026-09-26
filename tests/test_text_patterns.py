import youtube_pdca.text_patterns as text_patterns
from youtube_pdca.text_patterns import extract_frequent_keywords, merge_keyword_counts


def test_extract_frequent_keywords_does_not_split_long_vowel_words():
    # Janomeが利用可能な場合、「ニュース」のような長音を含む単語が分断されないことを確認する
    result = extract_frequent_keywords(["速報ニュースまとめ", "今日のニュース解説"])
    words = {w for w, _ in result}
    assert "ニュース" in words


def test_extract_frequent_keywords_excludes_particles_and_short_tokens():
    result = extract_frequent_keywords(["今日は速報を解説する"])
    words = {w for w, _ in result}
    assert "は" not in words
    assert "を" not in words


def test_extract_frequent_keywords_fallback_without_janome(monkeypatch):
    monkeypatch.setattr(text_patterns, "_tokenizer", None)
    result = extract_frequent_keywords(["速報ニュース まとめ", "速報ニュース 解説"])
    words = {w for w, _ in result}
    assert "速報ニュース" in words


def test_merge_keyword_counts_sums_duplicate_words():
    merged = merge_keyword_counts([("速報", 3), ("解説", 2), ("速報", 1)])
    assert dict(merged)["速報"] == 4
    assert dict(merged)["解説"] == 2


def test_merge_keyword_counts_respects_top_n():
    pairs = [(f"word{i}", i) for i in range(20)]
    merged = merge_keyword_counts(pairs, top_n=5)
    assert len(merged) == 5
