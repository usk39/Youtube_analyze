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


def test_compute_gap_with_custom_labels():
    labels = {"avg_brightness": "明度"}
    own = {"avg_brightness": 100}
    benchmark = {"avg_brightness": 150}
    gaps = compute_gap(own, benchmark, labels=labels)
    assert set(gaps.keys()) == {"avg_brightness"}
    assert gaps["avg_brightness"]["label"] == "明度"
    assert gaps["avg_brightness"]["diff"] == 50


def test_aggregate_competitor_benchmark_with_custom_keys():
    c1 = {"avg_brightness": 100, "avg_saturation": 0.2}
    c2 = {"avg_brightness": 200, "avg_saturation": 0.4}
    benchmark = aggregate_competitor_benchmark([c1, c2], keys=["avg_brightness"])
    assert benchmark == {"avg_brightness": 150}


def test_compute_trend_with_custom_labels():
    labels = {"avg_hashtag_count": "ハッシュタグ数"}
    prev = {"avg_hashtag_count": 2}
    cur = {"avg_hashtag_count": 4}
    trend = compute_trend(cur, prev, labels=labels)
    assert set(trend.keys()) == {"avg_hashtag_count"}
    assert trend["avg_hashtag_count"]["diff"] == 2
