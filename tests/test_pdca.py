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
