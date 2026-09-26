import io

import pytest
from PIL import Image

from youtube_pdca.thumbnail_analysis import (
    ThumbnailAnalysis,
    analyze_thumbnail_bytes,
    best_thumbnail_url,
    summarize_thumbnails,
)


def _make_png_bytes(color: tuple[int, int, int], size=(64, 36)) -> bytes:
    image = Image.new("RGB", size, color)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_best_thumbnail_url_prefers_higher_quality():
    thumbnails = {
        "default": {"url": "https://example.com/default.jpg"},
        "high": {"url": "https://example.com/high.jpg"},
        "maxres": {"url": "https://example.com/maxres.jpg"},
    }
    assert best_thumbnail_url(thumbnails) == "https://example.com/maxres.jpg"


def test_best_thumbnail_url_falls_back_when_missing():
    assert best_thumbnail_url({"default": {"url": "https://example.com/default.jpg"}}) == "https://example.com/default.jpg"
    assert best_thumbnail_url({}) is None


def test_analyze_thumbnail_bytes_bright_solid_color():
    image_bytes = _make_png_bytes((255, 255, 255))
    result = analyze_thumbnail_bytes("v1", "https://example.com/v1.jpg", image_bytes)

    assert isinstance(result, ThumbnailAnalysis)
    assert result.width == 64
    assert result.height == 36
    assert result.brightness > 200  # ほぼ白なので明度は高い
    assert 0.0 <= result.text_density_score <= 1.0


def test_analyze_thumbnail_bytes_solid_color_has_low_text_density():
    # 単色画像はエッジがほぼ無いため、文字量スコアは低くなるはず
    image_bytes = _make_png_bytes((10, 20, 200))
    result = analyze_thumbnail_bytes("v2", "https://example.com/v2.jpg", image_bytes)
    assert result.text_density_score < 0.1


def test_summarize_thumbnails_empty():
    summary = summarize_thumbnails([])
    assert summary["sample_size"] == 0
    assert summary["avg_brightness"] == 0


def test_summarize_thumbnails_averages_values():
    analyses = [
        ThumbnailAnalysis(video_id="v1", url="u1", width=10, height=10, brightness=100, saturation=0.2),
        ThumbnailAnalysis(video_id="v2", url="u2", width=10, height=10, brightness=200, saturation=0.4),
    ]
    summary = summarize_thumbnails(analyses)
    assert summary["sample_size"] == 2
    assert summary["avg_brightness"] == 150
    assert summary["avg_saturation"] == pytest.approx(0.3)
