from __future__ import annotations

import re
from collections import Counter

# 「ー」(長音符)は「ニュース」等の単語内に頻出するため区切り文字に含めない
_SEPARATORS = re.compile(r"[\s\|｜/／\-・,、。!?！？【】\[\]()（）:：]+")
_STOPWORDS = {
    "の", "に", "は", "を", "が", "で", "と", "も", "や", "た", "て",
    "です", "ます", "この", "その", "する", "した", "から", "まで",
    "ある", "いる", "こと", "など",
}


def extract_frequent_keywords(titles: list[str], top_n: int = 15) -> list[tuple[str, int]]:
    """動画タイトル群から頻出ワードを簡易的に抽出する(簡易分割・形態素解析なし)。"""
    counter: Counter[str] = Counter()
    for title in titles:
        for token in _SEPARATORS.split(title):
            token = token.strip()
            if len(token) < 2 or token in _STOPWORDS:
                continue
            counter[token] += 1
    return counter.most_common(top_n)
