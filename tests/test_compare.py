from youtube_pdca.compare import aggregate_competitor_benchmark, compute_gap, compute_trend


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


def test_aggregate_competitor_benchmark():
    c1 = base_summary(avg_views=2000)
    c2 = base_summary(avg_views=4000)
    benchmark = aggregate_competitor_benchmark([c1, c2])
    assert benchmark["avg_views"] == 3000


def test_aggregate_competitor_benchmark_empty():
    assert aggregate_competitor_benchmark([]) == {}


def test_compute_gap():
    own = base_summary(avg_views=1000, upload_frequency_per_week=2)
    benchmark = base_summary(avg_views=2000, upload_frequency_per_week=4)
    gaps = compute_gap(own, benchmark)
    assert gaps["avg_views"]["diff"] == 1000
    assert gaps["avg_views"]["diff_pct"] == 100
    assert gaps["upload_frequency_per_week"]["diff_pct"] == 100


def test_compute_trend_none():
    own = base_summary()
    assert compute_trend(own, None) is None


def test_compute_trend():
    prev = base_summary(avg_views=1000)
    cur = base_summary(avg_views=1200)
    trend = compute_trend(cur, prev)
    assert trend["avg_views"]["diff"] == 200
    assert round(trend["avg_views"]["diff_pct"], 2) == 20.0
