from youtube_pdca.pdca import _generate_act_items
from youtube_pdca.compare import compute_gap


def base_summary(**overrides):
    summary = {
        "avg_views": 1000,
        "avg_engagement_rate": 0.05,
        "avg_duration_seconds": 600,
        "avg_title_length": 20,
        "pct_titles_with_number": 0.3,
        "pct_titles_question": 0.1,
        "avg_tags_count": 5,
        "upload_frequency_per_week": 3,
    }
    summary.update(overrides)
    return summary


def test_generate_act_items_flags_frequency_gap():
    own = base_summary(upload_frequency_per_week=2)
    benchmark = base_summary(upload_frequency_per_week=5)
    gaps = compute_gap(own, benchmark)
    items = _generate_act_items(gaps, None, [], [])
    assert any("投稿頻度" in item for item in items)


def test_generate_act_items_no_gap_returns_maintain_message():
    own = base_summary()
    benchmark = base_summary()
    gaps = compute_gap(own, benchmark)
    items = _generate_act_items(gaps, None, [], [])
    assert len(items) == 1
    assert "維持" in items[0]


def test_generate_act_items_includes_missing_keywords():
    own = base_summary()
    benchmark = base_summary()
    gaps = compute_gap(own, benchmark)
    own_keywords = [("速報", 3)]
    competitor_keywords = [("速報", 5), ("徹底解説", 4)]
    items = _generate_act_items(gaps, None, own_keywords, competitor_keywords)
    assert any("徹底解説" in item for item in items)


def test_generate_act_items_flags_thumbnail_text_density_gap():
    own = base_summary()
    benchmark = base_summary()
    gaps = compute_gap(own, benchmark)
    thumbnail_gaps = {
        "avg_text_density_score": {
            "label": "サムネイル文字・情報量スコア(推定, 0-1)",
            "own": 0.1,
            "benchmark": 0.5,
            "diff": 0.4,
            "diff_pct": 400.0,
        }
    }
    items = _generate_act_items(gaps, None, [], [], thumbnail_gaps=thumbnail_gaps)
    assert any("サムネイル" in item for item in items)


def test_generate_act_items_flags_description_cta_gap():
    own = base_summary()
    benchmark = base_summary()
    gaps = compute_gap(own, benchmark)
    description_gaps = {
        "pct_with_cta": {
            "label": "登録/高評価/コメント誘導の文言を含む割合",
            "own": 0.1,
            "benchmark": 0.8,
            "diff": 0.7,
            "diff_pct": 700.0,
        }
    }
    items = _generate_act_items(gaps, None, [], [], description_gaps=description_gaps)
    assert any("概要欄" in item for item in items)


def test_generate_act_items_includes_missing_comment_keywords():
    own = base_summary()
    benchmark = base_summary()
    gaps = compute_gap(own, benchmark)
    items = _generate_act_items(
        gaps,
        None,
        [],
        [],
        own_comment_keywords=[("面白い", 2)],
        competitor_comment_keywords=[("面白い", 3), ("感動した", 5)],
    )
    assert any("感動した" in item for item in items)
