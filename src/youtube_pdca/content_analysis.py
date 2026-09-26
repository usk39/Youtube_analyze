from __future__ import annotations

import re
from dataclasses import dataclass, field

from .text_patterns import extract_frequent_keywords

DESCRIPTION_METRIC_LABELS = {
    "avg_length": "概要欄の平均文字数",
    "avg_hashtag_count": "概要欄の平均ハッシュタグ数",
    "pct_with_cta": "登録/高評価/コメント誘導の文言を含む割合",
}

_HASHTAG_RE = re.compile(r"#\S+")
_URL_RE = re.compile(r"https?://\S+")

# CTA(Call To Action)として概要欄に含まれているかを判定するキーワード
_CTA_KEYWORDS = {
    "登録": ["チャンネル登録", "登録よろしく", "サブスクライブ", "subscribe"],
    "高評価": ["高評価", "いいね", "グッドボタン", "like"],
    "コメント": ["コメント", "感想", "教えて"],
}


@dataclass
class DescriptionMetrics:
    video_id: str
    length: int
    hashtag_count: int
    url_count: int
    cta_flags: dict[str, bool] = field(default_factory=dict)

    @property
    def has_any_cta(self) -> bool:
        return any(self.cta_flags.values())


def analyze_description(video_id: str, description: str | None) -> DescriptionMetrics:
    description = description or ""
    cta_flags = {
        label: any(keyword in description for keyword in keywords) for label, keywords in _CTA_KEYWORDS.items()
    }
    return DescriptionMetrics(
        video_id=video_id,
        length=len(description),
        hashtag_count=len(_HASHTAG_RE.findall(description)),
        url_count=len(_URL_RE.findall(description)),
        cta_flags=cta_flags,
    )


def summarize_descriptions(analyses: list[DescriptionMetrics]) -> dict:
    n = len(analyses)
    if n == 0:
        return {"sample_size": 0, "avg_length": 0, "avg_hashtag_count": 0, "avg_url_count": 0, "pct_with_cta": 0}
    return {
        "sample_size": n,
        "avg_length": sum(a.length for a in analyses) / n,
        "avg_hashtag_count": sum(a.hashtag_count for a in analyses) / n,
        "avg_url_count": sum(a.url_count for a in analyses) / n,
        "pct_with_cta": sum(1 for a in analyses if a.has_any_cta) / n,
    }


def extract_comment_keywords(comments: list[str], top_n: int = 15) -> list[tuple[str, int]]:
    """コメント本文の頻出ワードを抽出する(視聴者が実際に反応している内容の把握用)。"""
    return extract_frequent_keywords(comments, top_n=top_n)
