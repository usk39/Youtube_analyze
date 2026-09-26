from __future__ import annotations

import re
from collections import Counter

try:
    from janome.tokenizer import Tokenizer as _JanomeTokenizer

    _tokenizer: "_JanomeTokenizer | None" = _JanomeTokenizer()
except Exception:  # pragma: no cover - janome未インストール時のフォールバック
    _tokenizer = None

# 「ー」(長音符)は「ニュース」等の単語内に頻出するため区切り文字に含めない(簡易分割フォールバック用)
_SEPARATORS = re.compile(r"[\s\|｜/／\-・,、。!?！？【】\[\]()（）:：]+")
_STOPWORDS = {
    "の", "に", "は", "を", "が", "で", "と", "も", "や", "た", "て",
    "です", "ます", "この", "その", "する", "した", "から", "まで",
    "ある", "いる", "こと", "など", "これ", "それ", "とき", "もの",
}
# Janomeの品詞細分類のうち、キーワードとして有用度が低いものは除外する
_EXCLUDED_SUBCATEGORIES = {"代名詞", "非自立", "接尾", "副詞可能"}


def _simple_split(title: str) -> list[str]:
    """Janomeが利用できない場合の簡易的な区切り文字分割。"""
    return [token.strip() for token in _SEPARATORS.split(title) if token.strip()]


def _tokenize_with_janome(title: str) -> list[str]:
    """Janomeで形態素解析し、意味のある名詞のみを抽出する。"""
    tokens = []
    for token in _tokenizer.tokenize(title):
        parts = token.part_of_speech.split(",")
        pos = parts[0]
        subpos = parts[1] if len(parts) > 1 else ""
        if pos != "名詞" or subpos in _EXCLUDED_SUBCATEGORIES:
            continue
        tokens.append(token.surface)
    return tokens


def extract_frequent_keywords(titles: list[str], top_n: int = 15) -> list[tuple[str, int]]:
    """動画タイトル群から頻出ワードを抽出する。

    Janomeがインストールされている場合は形態素解析で名詞を抽出し、
    インストールされていない場合は区切り文字による簡易分割にフォールバックする。
    """
    counter: Counter[str] = Counter()
    for title in titles:
        tokens = _tokenize_with_janome(title) if _tokenizer is not None else _simple_split(title)
        for token in tokens:
            if len(token) < 2 or token in _STOPWORDS:
                continue
            counter[token] += 1
    return counter.most_common(top_n)


def merge_keyword_counts(keyword_counts: list[tuple[str, int]], top_n: int = 15) -> list[tuple[str, int]]:
    """複数チャンネル分のキーワード集計結果(単語, 件数)を合算して再集計する。"""
    counter: Counter[str] = Counter()
    for word, count in keyword_counts:
        counter[word] += count
    return counter.most_common(top_n)
