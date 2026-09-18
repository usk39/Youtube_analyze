from __future__ import annotations


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"# YouTube自動PDCAレポート (サイクル{report['cycle']})")
    lines.append("")
    lines.append(f"実行日時: {report['run_at']}")
    lines.append("")

    lines.append("## Plan（今回取り組む目標）")
    for goal in report["plan"]:
        lines.append(f"- {goal}")
    lines.append("")

    own = report["own_summary"]
    lines.append("## Do（データ取得結果）")
    lines.append(f"### 自分のチャンネル: {own.get('channel_title')}")
    lines.append(f"- 登録者数: {own.get('subscriber_count', 0):,}")
    lines.append(f"- 分析対象動画数: {own.get('sample_size', 0)}本")
    lines.append(f"- 平均再生数: {own.get('avg_views', 0):,.0f}")
    lines.append(f"- 平均エンゲージメント率: {_fmt_pct(own.get('avg_engagement_rate', 0))}")
    lines.append(f"- 週間投稿頻度: {own.get('upload_frequency_per_week', 0):.2f}本/週")
    lines.append(f"- 平均動画時間: {own.get('avg_duration_seconds', 0) / 60:.1f}分")
    lines.append("")

    competitor_summaries = report.get("competitor_summaries") or []
    if competitor_summaries:
        lines.append("### 競合チャンネル")
        lines.append("| チャンネル名 | 登録者数 | 平均再生数 | エンゲージメント率 | 週間投稿頻度 |")
        lines.append("|---|---|---|---|---|")
        for c in competitor_summaries:
            lines.append(
                f"| {c.get('channel_title')} | {c.get('subscriber_count', 0):,} | "
                f"{c.get('avg_views', 0):,.0f} | {_fmt_pct(c.get('avg_engagement_rate', 0))} | "
                f"{c.get('upload_frequency_per_week', 0):.2f}本/週 |"
            )
        lines.append("")

    lines.append("## Check（比較・分析）")
    gaps = report.get("gaps") or {}
    if gaps:
        lines.append("| 指標 | 自分 | 競合平均 | 差分(%) |")
        lines.append("|---|---|---|---|")
        for g in gaps.values():
            lines.append(f"| {g['label']} | {g['own']:.2f} | {g['benchmark']:.2f} | {g['diff_pct']:+.1f}% |")
        lines.append("")
    else:
        lines.append("競合データがないため比較を実施できませんでした。`config/channels.yaml` に競合チャンネルを設定してください。")
        lines.append("")

    trend = report.get("trend")
    if trend:
        lines.append("### 前回サイクルからの推移")
        lines.append("| 指標 | 前回 | 今回 | 変化率 |")
        lines.append("|---|---|---|---|")
        for t in trend.values():
            lines.append(f"| {t['label']} | {t['previous']:.2f} | {t['current']:.2f} | {t['diff_pct']:+.1f}% |")
        lines.append("")

    own_kw = report.get("own_keywords") or []
    comp_kw = report.get("competitor_keywords") or []
    if own_kw or comp_kw:
        lines.append("### 人気動画タイトルの頻出ワード")
        lines.append(f"- 自分: {', '.join(f'{w}({c})' for w, c in own_kw[:10]) or 'なし'}")
        lines.append(f"- 競合: {', '.join(f'{w}({c})' for w, c in comp_kw[:10]) or 'なし'}")
        lines.append("")

    lines.append("## Act（次のアクション）")
    for item in report["act"]:
        lines.append(f"- [ ] {item}")
    lines.append("")
    lines.append("> 次回サイクルでは、このActの内容が新たなPlanとして自動的に引き継がれます。")

    return "\n".join(lines)
