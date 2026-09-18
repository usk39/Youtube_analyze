# YouTube自動PDCA

自分のYouTubeチャンネルと、伸びているライバルチャンネルを定期的に比較分析し、
「動画作成スキルをどう改善すべきか」を自動で提案し続けるツールです。

## PDCAの回し方

| フェーズ | 内容 |
|---|---|
| **Plan** | 前回サイクルの Act（改善アクション）が、そのまま今回の Plan（目標）として引き継がれる |
| **Do** | YouTube Data API v3 で、自分のチャンネルと競合チャンネルの最新動画データを取得する |
| **Check** | 自分 vs 競合平均のギャップ分析、および前回サイクルからの推移（トレンド）を分析する |
| **Act** | ギャップとトレンドをもとに、次に取るべき具体的な改善アクションを自動生成し、次回のPlanとして保存する |

`data/pdca_state.json` にサイクルの状態（現在の目標・履歴）が保存され、
`data/snapshots/` に毎回のチャンネルデータのスナップショットが蓄積されるため、
実行を重ねるほど「前回からどう変化したか」の精度が上がっていきます。

## セットアップ

### 1. YouTube Data API キーを取得する

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials) でプロジェクトを作成
2. 「YouTube Data API v3」を有効化
3. APIキーを発行する

### 2. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数を設定

```bash
cp .env.example .env
# .env を開いて YOUTUBE_API_KEY=xxxx を設定
```

### 4. チャンネルを設定する

`config/channels.yaml` を編集し、自分のチャンネルと、比較したいライバルチャンネルの
URL（`https://www.youtube.com/@handle` 形式や `/channel/UCxxxx` 形式など）を設定します。

```yaml
own_channel:
  url: "https://www.youtube.com/@your_channel_handle"

competitor_channels:
  - url: "https://www.youtube.com/@competitor_channel_1"
  - url: "https://www.youtube.com/@competitor_channel_2"

analysis:
  max_videos_per_channel: 30
  top_n_for_pattern: 10
```

## 実行方法

```bash
python scripts/run_pdca.py
```

実行すると:
- `data/snapshots/` に今回取得したチャンネル・動画データのスナップショットが保存される
- `data/reports/` に Plan → Do → Check → Act の全フェーズをまとめた Markdown レポートが生成される
- `data/pdca_state.json` の目標（Plan）が今回の Act 内容で更新され、次回実行時に引き継がれる

## 分析している指標

- 平均再生数・中央値
- エンゲージメント率（(高評価数 + コメント数) / 再生数）
- 週間投稿頻度
- 平均動画時間
- タイトルの平均文字数・数字を含む割合・疑問形の割合
- 平均タグ数
- 人気動画タイトルの頻出ワード（自分 vs 競合、簡易分割による抽出）

これらを「自分の直近動画 vs 競合チャンネル平均」および「自分の今回 vs 前回サイクル」の
2軸で比較し、差が一定のしきい値（`src/youtube_pdca/pdca.py` の `*_THRESHOLD_PCT`）を
超えている項目について、具体的な改善アクションを文章で生成します。

## GitHub Actionsによる自動実行

`.github/workflows/pdca.yml` により、毎週月曜9:00(JST)に自動でPDCAサイクルが実行されます。

- 生成されたスナップショット・レポート・状態ファイルは自動でリポジトリにコミットされる
- 最新レポートの内容でGitHub Issueが自動作成される

利用するには、リポジトリの Settings → Secrets and variables → Actions で
`YOUTUBE_API_KEY` を Secret として登録してください。

> **注意:** `schedule` トリガーはデフォルトブランチ上のワークフローのみ実行されます。
> 動作確認したい場合は Actions タブから `workflow_dispatch` で手動実行してください。

## テストの実行

```bash
pip install -r requirements-dev.txt
pytest
```

## 制限事項・拡張のアイデア

- タイトルの頻出ワード抽出は簡易的な区切り文字分割によるもので、本格的な日本語形態素解析
  （[Janome](https://github.com/mocobeta/janome) や MeCab など）を組み込むとより精度が上がります
- サムネイル画像そのものの分析（文字量・色使いなど）は未対応です。サムネイルURLは
  `snippet.thumbnails` から取得可能なので、画像解析ライブラリと組み合わせて拡張できます
- 現在は再生数・エンゲージメント等の「型」の比較のみですが、動画の説明文やコメント欄の
  内容分析を加えることで、より踏み込んだ企画提案も可能です
