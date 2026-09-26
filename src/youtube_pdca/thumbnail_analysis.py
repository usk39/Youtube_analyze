from __future__ import annotations

import io
import urllib.request
from dataclasses import dataclass, field

try:
    from PIL import Image, ImageFilter
except Exception:  # pragma: no cover - Pillow未インストール時のフォールバック
    Image = None
    ImageFilter = None

try:
    import pytesseract  # 任意。インストールされていればOCRで実際の文字数を測る
except Exception:  # pragma: no cover
    pytesseract = None

THUMBNAIL_METRIC_LABELS = {
    "avg_brightness": "サムネイル平均明度(0-255)",
    "avg_saturation": "サムネイル平均彩度(0-1)",
    "avg_text_density_score": "サムネイル文字・情報量スコア(推定, 0-1)",
}

_THUMBNAIL_QUALITY_ORDER = ("maxres", "standard", "high", "medium", "default")

# エッジ検出で「文字/情報量が多い」と判定するグレースケール輝度差のしきい値
_EDGE_THRESHOLD = 40


def best_thumbnail_url(thumbnails: dict) -> str | None:
    for quality in _THUMBNAIL_QUALITY_ORDER:
        entry = thumbnails.get(quality)
        if entry and entry.get("url"):
            return entry["url"]
    return None


@dataclass
class ThumbnailAnalysis:
    video_id: str
    url: str
    width: int
    height: int
    brightness: float
    saturation: float
    dominant_colors: list[tuple[int, int, int]] = field(default_factory=list)
    text_density_score: float = 0.0
    ocr_text: str | None = None
    ocr_char_count: int = 0


def fetch_thumbnail_bytes(url: str, timeout: int = 10) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (公開CDNの画像取得)
        return response.read()


def analyze_thumbnail_bytes(video_id: str, url: str, image_bytes: bytes) -> ThumbnailAnalysis:
    if Image is None:
        raise RuntimeError("Pillow がインストールされていません。`pip install Pillow` を実行してください")

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = image.size

    grayscale = image.convert("L")
    gray_pixels = list(grayscale.getdata())
    brightness = sum(gray_pixels) / len(gray_pixels)

    small = image.resize((min(width, 100), min(height, 100)))
    hsv_pixels = list(small.convert("HSV").getdata())
    saturation = (sum(p[1] for p in hsv_pixels) / len(hsv_pixels)) / 255

    quantized = small.quantize(colors=5)
    palette = quantized.getpalette() or []
    dominant_colors = []
    for count, index in sorted(quantized.getcolors() or [], reverse=True)[:5]:
        r, g, b = palette[index * 3 : index * 3 + 3]
        dominant_colors.append((r, g, b))

    edges = grayscale.filter(ImageFilter.FIND_EDGES)
    edge_pixels = list(edges.getdata())
    text_density_score = sum(1 for p in edge_pixels if p > _EDGE_THRESHOLD) / len(edge_pixels)

    ocr_text = None
    ocr_char_count = 0
    if pytesseract is not None:
        try:
            ocr_text = pytesseract.image_to_string(image, lang="jpn+eng").strip()
            ocr_char_count = len(ocr_text.replace("\n", "").replace(" ", ""))
        except Exception:
            ocr_text = None
            ocr_char_count = 0

    return ThumbnailAnalysis(
        video_id=video_id,
        url=url,
        width=width,
        height=height,
        brightness=brightness,
        saturation=saturation,
        dominant_colors=dominant_colors,
        text_density_score=text_density_score,
        ocr_text=ocr_text,
        ocr_char_count=ocr_char_count,
    )


def analyze_thumbnail(video_id: str, url: str, timeout: int = 10) -> ThumbnailAnalysis:
    image_bytes = fetch_thumbnail_bytes(url, timeout=timeout)
    return analyze_thumbnail_bytes(video_id, url, image_bytes)


def summarize_thumbnails(analyses: list[ThumbnailAnalysis]) -> dict:
    n = len(analyses)
    if n == 0:
        return {
            "sample_size": 0,
            "avg_brightness": 0,
            "avg_saturation": 0,
            "avg_text_density_score": 0,
            "avg_ocr_char_count": 0,
        }
    return {
        "sample_size": n,
        "avg_brightness": sum(a.brightness for a in analyses) / n,
        "avg_saturation": sum(a.saturation for a in analyses) / n,
        "avg_text_density_score": sum(a.text_density_score for a in analyses) / n,
        "avg_ocr_char_count": sum(a.ocr_char_count for a in analyses) / n,
    }
