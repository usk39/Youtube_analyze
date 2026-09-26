from youtube_pdca.content_analysis import (
    DescriptionMetrics,
    analyze_description,
    extract_comment_keywords,
    summarize_descriptions,
)


def test_analyze_description_detects_cta_and_hashtags():
    description = "今日はニュース解説です！ チャンネル登録・高評価よろしくお願いします #ニュース #解説 https://example.com"
    result = analyze_description("v1", description)

    assert result.hashtag_count == 2
    assert result.url_count == 1
    assert result.cta_flags["登録"] is True
    assert result.cta_flags["高評価"] is True
    assert result.has_any_cta is True


def test_analyze_description_no_cta():
    result = analyze_description("v1", "今日の動画では速報ニュースを紹介します。")
    assert result.has_any_cta is False
    assert result.hashtag_count == 0


def test_analyze_description_handles_none():
    result = analyze_description("v1", None)
    assert result.length == 0
    assert result.has_any_cta is False


def test_summarize_descriptions_empty():
    summary = summarize_descriptions([])
    assert summary["sample_size"] == 0
    assert summary["pct_with_cta"] == 0


def test_summarize_descriptions_pct_with_cta():
    analyses = [
        DescriptionMetrics(video_id="v1", length=10, hashtag_count=1, url_count=0, cta_flags={"登録": True}),
        DescriptionMetrics(video_id="v2", length=20, hashtag_count=0, url_count=0, cta_flags={"登録": False}),
    ]
    summary = summarize_descriptions(analyses)
    assert summary["sample_size"] == 2
    assert summary["pct_with_cta"] == 0.5
    assert summary["avg_length"] == 15


def test_extract_comment_keywords_returns_frequent_words():
    comments = ["このニュースは面白い", "ニュースの解説がわかりやすい"]
    result = extract_comment_keywords(comments)
    words = {w for w, _ in result}
    assert "ニュース" in words
