# 📈 SNS発信に使える Streamlit 株価アプリ3本

`Streamlit` と `yfinance` だけで作る、SNS発信に使える日本株向けアプリ3本のサンプルコードです。いずれも 100〜150 行程度の単一ファイルで完結します。

| # | アプリ | ファイル | 主な機能 |
|:--|:--|:--|:--|
| 1 | **5分足チャート** | `app_chart.py` | 複数銘柄のローソク足＋日足を1画面で確認 |
| 2 | **SNSサムネイル生成** | `app_thumbnail_dark.py` / `app_thumbnail_normal.py` | 株価チャートを PNG 画像として出力（ダーク/ライト2種類） |
| 3 | **AIプロンプトビルダー** | `app_prompt.py` | テクニカル指標を埋め込んだ Claude / ChatGPT 用プロンプトを生成 |

<br>

## 必要要件

- Python 3.10 以上

### 依存ライブラリ

```
streamlit, pandas, numpy, altair, matplotlib, yfinance
```

<br>

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/tomo-account/00_sample_app.git
cd 00_sample_app

# 依存ライブラリをインストール
pip install -r requirements.txt

# 任意のアプリを起動
streamlit run app_chart.py
streamlit run app_thumbnail_dark.py
streamlit run app_thumbnail_normal.py
streamlit run app_prompt.py
```

<br>

## 1. 5分足チャート — `app_chart.py`

![](https://raw.githubusercontent.com/tomo-account/00_sample_app/refs/heads/main/image_chart.png)

複数銘柄の5分足ローソク足を一画面で並べて表示します。

- **縦の境界線**でギャップアップ・ギャップダウンを視覚的に把握しやすく
- 短期の値動きと中期トレンドを同一チャートで**同時に確認**できる構成
- **日別マトリクステーブル**で株価と騰落率の推移を一覧表示

**使い方：** 銘柄コードをカンマ・スペース・改行で複数入力、基準日と遡る日数を指定するだけ。

<br>

## 2. SNSサムネイル生成 — `app_thumbnail_dark.py` / `app_thumbnail_normal.py`

| ダーク版 | ライト版 |
|:--|:--|
| ![](https://raw.githubusercontent.com/tomo-account/00_sample_app/refs/heads/main/image_thumbnail_dark.png) | ![](https://raw.githubusercontent.com/tomo-account/00_sample_app/refs/heads/main/image_thumbnail_normal.png) |

X（旧Twitter）や note のサムネイル画像として使える株価チャートを生成します。

- ボタンひとつで **PNG ダウンロード**
- **Note のサムネイル**に最適なサイズ
- **ダーク版** と Google Finance に寄せた **ライト版** の2種類

**使い方：** 証券コードと右側に載せたいテキスト（タイトル＋見出し）を入力 → 「Generate」ボタン。

<br>

## 3. AIプロンプトビルダー — `app_prompt.py`

![](https://raw.githubusercontent.com/tomo-account/00_sample_app/refs/heads/main/image_prompt.png)

株クラ向け X 投稿の3パターンを生成するための AI 用プロンプトをビルドします。

- 株クラ向け **X 投稿を3パターン**出力するプロンプト
- RSI / MACD / ボリンジャーバンド / 移動平均などの **テクニカル指標を埋め込み**
- ニュース・注目点を **任意で追加** できる入力欄

**使い方：** 証券コードとニュース・注目点を入力 → 「プロンプトを作成」ボタンで生成されたテキストを Claude / ChatGPT に貼り付け。

<br>

## データの取り扱いについて

- 本アプリは個人利用および学習を目的としたツールであり、投資勧誘を目的としたものではありません。
- `yfinance` ライブラリを使用しています。利用にあたっては、Yahoo! の規約を遵守してください。
- 短時間での大量取得はサーバーに負担がかかります。APIのレート制限を守り、過度なリクエストは避けてください。

### Yahoo! 規約類

- [Yahoo! Finance Terms of Service](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html)
- [Yahoo! Developer API Terms of Use](https://policies.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.htm)
- [Yahoo! 権利関係ページ](https://legal.yahoo.com/us/en/yahoo/permissions/requests/index.html)

<br>

## ⚠️ 免責事項

- **データの正確性**：取得データは正確性や即時性を保証しません。
- **損害への責任**：本ツールの利用により生じたいかなる損害についても、制作者は一切の責任を負いません。

<br>

## ライセンス

MIT
