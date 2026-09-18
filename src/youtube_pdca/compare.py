from __future__ import annotations

METRIC_LABELS = {
    "avg_views": "平均再生数",
    "avg_engagement_rate": "エンゲージメント率",
    "avg_duration_seconds": "平均動画時間(秒)",
    "avg_title_length": "平均タイトル文字数",
    "pct_titles_with_number": "数字入りタイトル率",
    "pct_titles_question": "疑問形タイトル率",
    "avg_tags_count": "平均タグ数",
    "upload_frequency_per_week": "週間投稿頻度",
}


def compute_gap(own_summary: dict, benchmark_summary: dict) -> dict:
    gaps = {}
    for key, label in METRIC_LABELS.items():
        own_val = own_summary.get(key, 0) or 0
        bench_val = benchmark_summary.get(key, 0) or 0
        diff = bench_val - own_val
        diff_pct = (diff / own_val * 100) if own_val else (100.0 if bench_val else 0.0)
        gaps[key] = {
            "label": label,
            "own": own_val,
            "benchmark": bench_val,
            "diff": diff,
            "diff_pct": diff_pct,
        }
    return gaps


def aggregate_competitor_benchmark(competitor_summaries: list[dict]) -> dict:
    if not competitor_summaries:
        return {}
    agg = {}
    for key in METRIC_LABELS:
        vals = [c.get(key, 0) or 0 for c in competitor_summaries]
        agg[key] = sum(vals) / len(vals)
    return agg


def compute_trend(current_summary: dict, previous_summary: dict | None) -> dict | None:
    if not previous_summary:
        return None
    trend = {}
    for key, label in METRIC_LABELS.items():
        cur = current_summary.get(key, 0) or 0
        prev = previous_summary.get(key, 0) or 0
        diff = cur - prev
        diff_pct = (diff / prev * 100) if prev else (100.0 if cur else 0.0)
        trend[key] = {"label": label, "previous": prev, "current": cur, "diff": diff, "diff_pct": diff_pct}
    return trend
