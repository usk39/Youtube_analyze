from youtube_pdca.metrics import compute_channel_summary, compute_video_metrics, parse_duration


def test_parse_duration():
    assert parse_duration("PT10M30S") == 630
    assert parse_duration("PT1H2M3S") == 3723
    assert parse_duration("PT45S") == 45
    assert parse_duration("PT0S") == 0
    assert parse_duration("") == 0


def make_video(video_id, title, views, likes, comments, duration, published_at, tags=None):
    return {
        "id": video_id,
        "snippet": {
            "title": title,
            "publishedAt": published_at,
            "tags": tags or [],
        },
        "statistics": {
            "viewCount": str(views),
            "likeCount": str(likes),
            "commentCount": str(comments),
        },
        "contentDetails": {"duration": duration},
    }


def test_compute_video_metrics():
    video = make_video(
        "v1", "2026年最新ニュース5選まとめ", 1000, 50, 10, "PT8M0S", "2026-01-01T00:00:00Z", tags=["a", "b"]
    )
    m = compute_video_metrics(video)
    assert m["views"] == 1000
    assert m["engagement_rate"] == (50 + 10) / 1000
    assert m["duration_seconds"] == 480
    assert m["has_number_in_title"] is True
    assert m["tags_count"] == 2


def test_compute_video_metrics_zero_views():
    video = make_video("v1", "タイトル", 0, 0, 0, "PT1M0S", "2026-01-01T00:00:00Z")
    m = compute_video_metrics(video)
    assert m["engagement_rate"] == 0.0


def test_compute_channel_summary_empty():
    summary = compute_channel_summary({"channel_id": "UCxxx", "title": "T"}, [])
    assert summary["sample_size"] == 0
    assert summary["avg_views"] == 0
    assert summary["top_videos"] == []


def test_compute_channel_summary():
    videos = [
        make_video("v1", "タイトル1", 100, 5, 1, "PT5M0S", "2026-01-01T00:00:00Z"),
        make_video("v2", "タイトル2 3選", 300, 15, 3, "PT10M0S", "2026-01-08T00:00:00Z"),
    ]
    metrics = [compute_video_metrics(v) for v in videos]
    summary = compute_channel_summary({"channel_id": "UCxxx", "title": "MyChannel"}, metrics, top_n=1)

    assert summary["sample_size"] == 2
    assert summary["avg_views"] == 200
    assert len(summary["top_videos"]) == 1
    assert summary["top_videos"][0]["video_id"] == "v2"
    assert summary["upload_frequency_per_week"] > 0
