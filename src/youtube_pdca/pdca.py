from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import snapshot_store as store
from . import youtube_client as yt
from .compare import aggregate_competitor_benchmark, compute_gap, compute_trend
from .config import AppConfig, ChannelConfig
from .content_analysis import (
    DESCRIPTION_METRIC_LABELS,
    analyze_description,
    extract_comment_keywords,
    summarize_descriptions,
)
from .metrics import compute_channel_summary, compute_video_metrics
from .text_patterns import extract_frequent_keywords, merge_keyword_counts
from .thumbnail_analysis import THUMBNAIL_METRIC_LABELS, analyze_thumbnail, summarize_thumbnails

STATE_FILENAME = "pdca_state.json"

# 「差が大きい」と判断するしきい値(%)。これを超えたら改善アクションを提案する。
FREQ_THRESHOLD_PCT = 15.0
ENGAGEMENT_THRESHOLD_PCT = 15.0
DURATION_THRESHOLD_PCT = 20.0
TITLE_NUMBER_THRESHOLD_PCT = 20.0
TITLE_LENGTH_THRESHOLD_PCT = 20.0
TAGS_THRESHOLD_PCT = 30.0
VIEWS_DECLINE_THRESHOLD_PCT = -10.0
TEXT_DENSITY_THRESHOLD_PCT = 25.0
BRIGHTNESS_THRESHOLD_PCT = 20.0
SATURATION_THRESHOLD_PCT = 20.0
CTA_THRESHOLD_PCT = 20.0
HASHTAG_THRESHOLD_PCT = 30.0


def _analyze_top_videos_extra(youtube, summary: dict, config: AppConfig) -> None:
    """上位動画についてサムネイル・概要欄・コメントを追加分析し、summaryに書き込む。"""
    top_videos = summary.get("top_videos", [])

    if config.analyze_thumbnails:
        thumbnail_analyses = []
        for video in top_videos[: config.thumbnails_per_channel]:
            thumbnail_url = video.get("thumbnail_url")
            if not thumbnail_url:
                continue
            try:
                thumbnail_analyses.append(analyze_thumbnail(video["video_id"], thumbnail_url))
            except Exception:
                continue
        summary["thumbnail_summary"] = summarize_thumbnails(thumbnail_analyses)
    else:
        summary["thumbnail_summary"] = summarize_thumbnails([])

    description_analyses = [
        analyze_description(video["video_id"], video.get("description", "")) for video in top_videos
    ]
    summary["description_summary"] = summarize_descriptions(description_analyses)

    if config.analyze_comments:
        comments: list[str] = []
        for video in top_videos[: config.videos_for_comment_analysis]:
            comments.extend(yt.get_top_comments(youtube, video["video_id"], max_results=config.comments_per_video))
        summary["comment_keywords"] = extract_comment_keywords(comments)
    else:
        summary["comment_keywords"] = []


def _fetch_channel_summary(youtube, channel_cfg: ChannelConfig, config: AppConfig) -> dict:
    channel_id = channel_cfg.channel_id or yt.resolve_channel_id(youtube, channel_cfg.identifier())
    stats = yt.get_channel_stats(youtube, channel_id)
    videos_raw = yt.get_recent_videos(youtube, stats["uploads_playlist_id"], config.max_videos_per_channel)
    video_metrics = [compute_video_metrics(v) for v in videos_raw]
    summary = compute_channel_summary(stats, video_metrics, top_n=config.top_n_for_pattern)
    _analyze_top_videos_extra(youtube, summary, config)
    return summary


def load_state(data_dir: Path) -> dict:
    path = Path(data_dir) / STATE_FILENAME
    if not path.exists():
        return {"cycle_count": 0, "current_goals": [], "history": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(data_dir: Path, state: dict) -> None:
    path = Path(data_dir) / STATE_FILENAME
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _generate_act_items(
    gaps: dict,
    trend: dict | None,
    own_keywords: list[tuple[str, int]],
    competitor_keywords: list[tuple[str, int]],
    thumbnail_gaps: dict | None = None,
    description_gaps: dict | None = None,
    own_comment_keywords: list[tuple[str, int]] | None = None,
    competitor_comment_keywords: list[tuple[str, int]] | None = None,
) -> list[str]:
    items: list[str] = []

    freq = gaps["upload_frequency_per_week"]
    if freq["diff_pct"] > FREQ_THRESHOLD_PCT:
        items.append(
            f"投稿頻度を週{freq['own']:.1f}本→週{freq['benchmark']:.1f}本に近づける"
            f"(競合平均は{freq['diff_pct']:.0f}%多く投稿している)"
        )

    eng = gaps["avg_engagement_rate"]
    if eng["diff_pct"] > ENGAGEMENT_THRESHOLD_PCT:
        items.append(
            f"エンゲージメント率を改善する(自分:{eng['own'] * 100:.2f}% / 競合平均:{eng['benchmark'] * 100:.2f}%)。"
            "動画内でコメント・高評価・チャンネル登録を呼びかけるタイミングと言い方を見直す"
        )

    dur = gaps["avg_duration_seconds"]
    if abs(dur["diff_pct"]) > DURATION_THRESHOLD_PCT:
        direction = "伸ばす" if dur["diff"] > 0 else "短くする"
        items.append(
            f"動画の平均尺を{direction}検討をする"
            f"(自分:{dur['own'] / 60:.1f}分 / 競合平均:{dur['benchmark'] / 60:.1f}分)"
        )

    num = gaps["pct_titles_with_number"]
    if num["diff_pct"] > TITLE_NUMBER_THRESHOLD_PCT:
        items.append(
            "タイトルに具体的な数字を入れる割合を増やす"
            f"(自分:{num['own'] * 100:.0f}% / 競合平均:{num['benchmark'] * 100:.0f}%)"
        )

    length = gaps["avg_title_length"]
    if abs(length["diff_pct"]) > TITLE_LENGTH_THRESHOLD_PCT:
        direction = "長く" if length["diff"] > 0 else "短く"
        items.append(
            f"タイトルの文字数を{direction}する"
            f"(自分:{length['own']:.0f}文字 / 競合平均:{length['benchmark']:.0f}文字)"
        )

    tags = gaps["avg_tags_count"]
    if tags["diff_pct"] > TAGS_THRESHOLD_PCT:
        items.append(
            f"動画タグの設定数を増やす(自分:平均{tags['own']:.1f}個 / 競合平均:平均{tags['benchmark']:.1f}個)"
        )

    own_words = {w for w, _ in own_keywords}
    missing_keywords = [w for w, _ in competitor_keywords if w not in own_words][:5]
    if missing_keywords:
        items.append(
            "競合の伸びている動画タイトルで頻出しているが自分は使えていないワードの活用を検討する: "
            + "、".join(missing_keywords)
        )

    if trend:
        views_trend = trend["avg_views"]
        if views_trend["diff_pct"] < VIEWS_DECLINE_THRESHOLD_PCT:
            items.append(
                f"前回サイクルより平均再生数が{abs(views_trend['diff_pct']):.0f}%低下している。"
                "直近投稿した動画のタイトル・サムネイル・投稿タイミングを見直す"
            )

    if thumbnail_gaps:
        text_density = thumbnail_gaps.get("avg_text_density_score")
        if text_density and abs(text_density["diff_pct"]) > TEXT_DENSITY_THRESHOLD_PCT:
            direction = "増やす(文字を大きくする・要素を追加する)" if text_density["diff"] > 0 else "減らす(シンプルな構図にする)"
            items.append(
                f"サムネイルの文字・情報量を{direction}検討をする"
                f"(推定スコア 自分:{text_density['own']:.2f} / 競合平均:{text_density['benchmark']:.2f})"
            )

        saturation = thumbnail_gaps.get("avg_saturation")
        if saturation and saturation["diff_pct"] > SATURATION_THRESHOLD_PCT:
            items.append(
                "サムネイルの彩度(色の鮮やかさ)を高め、目を引く配色を検討する"
                f"(自分:{saturation['own']:.2f} / 競合平均:{saturation['benchmark']:.2f})"
            )

        brightness = thumbnail_gaps.get("avg_brightness")
        if brightness and abs(brightness["diff_pct"]) > BRIGHTNESS_THRESHOLD_PCT:
            direction = "明るく" if brightness["diff"] > 0 else "暗くしてコントラストを強める方向で"
            items.append(
                f"サムネイルを{direction}する調整を検討する"
                f"(自分:{brightness['own']:.0f} / 競合平均:{brightness['benchmark']:.0f})"
            )

    if description_gaps:
        cta = description_gaps.get("pct_with_cta")
        if cta and cta["diff_pct"] > CTA_THRESHOLD_PCT:
            items.append(
                "概要欄にチャンネル登録・高評価・コメントを促す文言を入れる動画の割合を増やす"
                f"(自分:{cta['own'] * 100:.0f}% / 競合平均:{cta['benchmark'] * 100:.0f}%)"
            )

        hashtag = description_gaps.get("avg_hashtag_count")
        if hashtag and hashtag["diff_pct"] > HASHTAG_THRESHOLD_PCT:
            items.append(
                "概要欄に設定するハッシュタグの数を増やす"
                f"(自分:平均{hashtag['own']:.1f}個 / 競合平均:平均{hashtag['benchmark']:.1f}個)"
            )

    if own_comment_keywords is not None and competitor_comment_keywords:
        own_comment_words = {w for w, _ in own_comment_keywords}
        missing_comment_keywords = [w for w, _ in competitor_comment_keywords if w not in own_comment_words][:5]
        if missing_comment_keywords:
            items.append(
                "競合動画のコメント欄で視聴者がよく反応しているが、自分の動画のコメント欄では見られないワード: "
                + "、".join(missing_comment_keywords)
            )

    if not items:
        items.append("主要指標で競合との大きなギャップは見られない。現在の型を維持しつつ新しい企画で差別化を狙う")

    return items


def run_cycle(config: AppConfig, youtube, data_dir: Path) -> dict:
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    state = load_state(data_dir)

    # --- Plan: 前回サイクルのActが今回のPlan(目標)になる ---
    plan_goals = state.get("current_goals") or [
        "初回サイクルのため、まず自分と競合の現状データを取得しベースラインを作る"
    ]

    previous_own_summary = store.load_latest_snapshot(data_dir, "own")

    # --- Do: 最新データを取得する(動画の型・サムネイル・概要欄・コメントを含む) ---
    own_summary = _fetch_channel_summary(youtube, config.own_channel, config)
    store.save_snapshot(data_dir, "own", own_summary)

    competitor_summaries = [
        _fetch_channel_summary(youtube, comp_cfg, config) for comp_cfg in config.competitor_channels
    ]
    store.save_snapshot(data_dir, "competitors", {"channels": competitor_summaries})

    # --- Check: 競合との比較、前回サイクルからの推移を評価する ---
    benchmark = aggregate_competitor_benchmark(competitor_summaries)
    gaps = compute_gap(own_summary, benchmark) if benchmark else {}
    trend = compute_trend(own_summary, previous_own_summary)

    own_thumbnail_summary = own_summary.get("thumbnail_summary") or {}
    competitor_thumbnail_summaries = [c.get("thumbnail_summary") for c in competitor_summaries if c.get("thumbnail_summary")]
    thumbnail_benchmark = aggregate_competitor_benchmark(
        competitor_thumbnail_summaries, keys=list(THUMBNAIL_METRIC_LABELS)
    )
    thumbnail_gaps = (
        compute_gap(own_thumbnail_summary, thumbnail_benchmark, labels=THUMBNAIL_METRIC_LABELS)
        if thumbnail_benchmark
        else {}
    )

    own_description_summary = own_summary.get("description_summary") or {}
    competitor_description_summaries = [
        c.get("description_summary") for c in competitor_summaries if c.get("description_summary")
    ]
    description_benchmark = aggregate_competitor_benchmark(
        competitor_description_summaries, keys=list(DESCRIPTION_METRIC_LABELS)
    )
    description_gaps = (
        compute_gap(own_description_summary, description_benchmark, labels=DESCRIPTION_METRIC_LABELS)
        if description_benchmark
        else {}
    )

    own_top_titles = [v["title"] for v in own_summary.get("top_videos", [])]
    competitor_top_titles = [v["title"] for c in competitor_summaries for v in c.get("top_videos", [])]
    own_keywords = extract_frequent_keywords(own_top_titles)
    competitor_keywords = extract_frequent_keywords(competitor_top_titles)

    own_comment_keywords = own_summary.get("comment_keywords", [])
    competitor_comment_keywords = merge_keyword_counts(
        [pair for c in competitor_summaries for pair in c.get("comment_keywords", [])]
    )

    # --- Act: 次に取るべき具体的な改善アクションを生成し、次回サイクルのPlanとして保存する ---
    if gaps:
        act_items = _generate_act_items(
            gaps,
            trend,
            own_keywords,
            competitor_keywords,
            thumbnail_gaps=thumbnail_gaps,
            description_gaps=description_gaps,
            own_comment_keywords=own_comment_keywords,
            competitor_comment_keywords=competitor_comment_keywords,
        )
    else:
        act_items = ["競合チャンネルが設定されていないため比較できません。config/channels.yaml に競合チャンネルを追加してください"]

    cycle_count = state.get("cycle_count", 0) + 1
    now = datetime.now(timezone.utc).isoformat()
    state["cycle_count"] = cycle_count
    state["current_goals"] = act_items
    state.setdefault("history", []).append(
        {
            "cycle": cycle_count,
            "run_at": now,
            "goals_before": plan_goals,
            "act_items": act_items,
        }
    )
    save_state(data_dir, state)

    return {
        "cycle": cycle_count,
        "run_at": now,
        "plan": plan_goals,
        "own_summary": own_summary,
        "competitor_summaries": competitor_summaries,
        "benchmark": benchmark,
        "gaps": gaps,
        "trend": trend,
        "own_keywords": own_keywords,
        "competitor_keywords": competitor_keywords,
        "thumbnail_gaps": thumbnail_gaps,
        "description_gaps": description_gaps,
        "own_comment_keywords": own_comment_keywords,
        "competitor_comment_keywords": competitor_comment_keywords,
        "act": act_items,
    }
