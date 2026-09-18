#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402

from youtube_pdca.config import load_config  # noqa: E402
from youtube_pdca.pdca import run_cycle  # noqa: E402
from youtube_pdca.report import render_markdown  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="YouTube動画分析 自動PDCAツール")
    parser.add_argument("--config", default="config/channels.yaml", type=Path, help="チャンネル設定ファイル")
    parser.add_argument("--data-dir", default="data", type=Path, help="スナップショット・レポートの保存先")
    parser.add_argument("--api-key", default=None, help="YouTube Data API キー(未指定時は環境変数を使用)")
    args = parser.parse_args()

    load_dotenv()
    api_key = args.api_key or os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("エラー: YOUTUBE_API_KEY が設定されていません(.env に設定するか --api-key で指定してください)", file=sys.stderr)
        return 1

    config = load_config(args.config)
    youtube = build("youtube", "v3", developerKey=api_key)

    report = run_cycle(config, youtube, args.data_dir)
    markdown = render_markdown(report)

    reports_dir = args.data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    report_path = reports_dir / f"{date_str}_cycle{report['cycle']}.md"
    report_path.write_text(markdown, encoding="utf-8")

    print(markdown)
    print(f"\nレポートを保存しました: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
