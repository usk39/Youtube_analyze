from __future__ import annotations

import re
from datetime import datetime

_DURATION_RE = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


def parse_duration(duration: str) -> int:
    """ISO8601形式(PT#H#M#S)の動画時間を秒数に変換する。"""
    match = _DURATION_RE.match(duration or "")
    if not match:
        return 0
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def compute_video_metrics(video: dict) -> dict:
    snippet = video.get("snippet", {})
    stats = video.get("statistics", {})
    content = video.get("contentDetails", {})

    title = snippet.get("title", "")
    views = int(stats.get("viewCount", 0))
    likes = int(stats.get("likeCount", 0))
    comments = int(stats.get("commentCount", 0))
    tags = snippet.get("tags") or []

    return {
        "video_id": video.get("id"),
        "title": title,
        "published_at": snippet.get("publishedAt"),
        "views": views,
        "likes": likes,
        "comments": comments,
        "engagement_rate": (likes + comments) / views if views > 0 else 0.0,
        "duration_seconds": parse_duration(content.get("duration", "PT0S")),
        "title_length": len(title),
        "has_number_in_title": any(ch.isdigit() for ch in title),
        "is_question_title": ("?" in title) or ("？" in title),
        "tags_count": len(tags),
    }


def compute_channel_summary(channel_stats: dict, video_metrics: list[dict], top_n: int = 10) -> dict:
    base = {
        "channel_id": channel_stats.get("channel_id"),
        "channel_title": channel_stats.get("title"),
        "subscriber_count": channel_stats.get("subscriber_count", 0),
        "video_count_total": channel_stats.get("video_count", 0),
    }

    n = len(video_metrics)
    if n == 0:
        return {
            **base,
            "sample_size": 0,
            "avg_views": 0,
            "median_views": 0,
            "avg_engagement_rate": 0,
            "avg_duration_seconds": 0,
            "avg_title_length": 0,
            "pct_titles_with_number": 0,
            "pct_titles_question": 0,
            "avg_tags_count": 0,
            "upload_frequency_per_week": 0,
            "top_videos": [],
        }

    sorted_by_date = sorted(video_metrics, key=lambda v: v["published_at"])
    views_sorted = sorted(v["views"] for v in video_metrics)
    if n % 2:
        median_views = views_sorted[n // 2]
    else:
        median_views = (views_sorted[n // 2 - 1] + views_sorted[n // 2]) / 2

    oldest = _parse_iso(sorted_by_date[0]["published_at"])
    newest = _parse_iso(sorted_by_date[-1]["published_at"])
    span_days = max((newest - oldest).total_seconds() / 86400, 1)
    upload_frequency_per_week = (n / span_days) * 7

    top_videos = sorted(video_metrics, key=lambda v: v["views"], reverse=True)[:top_n]

    return {
        **base,
        "sample_size": n,
        "avg_views": sum(v["views"] for v in video_metrics) / n,
        "median_views": median_views,
        "avg_engagement_rate": sum(v["engagement_rate"] for v in video_metrics) / n,
        "avg_duration_seconds": sum(v["duration_seconds"] for v in video_metrics) / n,
        "avg_title_length": sum(v["title_length"] for v in video_metrics) / n,
        "pct_titles_with_number": sum(1 for v in video_metrics if v["has_number_in_title"]) / n,
        "pct_titles_question": sum(1 for v in video_metrics if v["is_question_title"]) / n,
        "avg_tags_count": sum(v["tags_count"] for v in video_metrics) / n,
        "upload_frequency_per_week": upload_frequency_per_week,
        "top_videos": top_videos,
    }
