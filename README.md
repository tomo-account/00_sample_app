# 📈 ５分足チャート

日本株の５分足チャートを表示する Streamlit アプリです。複数銘柄を同時に確認でき、ローソク足・出来高・日次騰落率をひとつの画面にまとめて表示します。

<br><br>

## 機能

- **５分足ローソク足チャート** — 指定日数分の足データを表示（前場・後場の区切り線付き）
- **日足ラインチャート** — 過去約６ヶ月の終値推移をサイドに表示
- **日次サマリテーブル** — 終値・騰落率（前日終値比）を日付ごとに表示
- **複数銘柄対応** — 銘柄コードをカンマ・スペース・改行区切りで複数入力可能
- **TOPIX銘柄辞書** — `data_j.xls` から銘柄名を自動取得
- **キャッシュ機能** — `yfinance` のデータを５分間キャッシュしてAPIコールを削減

<br><br>

## 必要要件

- Python 3.9 以上

### 依存ライブラリ

```
streamlit
pandas
altair
yfinance
openpyxl
xlrd
```

<br><br>

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# 依存ライブラリをインストール
pip install -r requirements.txt

# アプリを起動
streamlit run app.py
```

<br><br>

## データファイル

| ファイル | 説明 |
|---|---|
| `data_j.xls` | TOPIX採用銘柄の銘柄コード・銘柄名一覧。[JPX公式サイト](https://www.jpx.co.jp/markets/statistics-equities/misc/01.html) からダウンロードして `app.py` と同じディレクトリに配置してください。 |

> `data_j.xls` が存在しない場合でも動作しますが、銘柄名の代わりにコード＋`.T` が表示されます。

<br><br>

## 使い方

1. **銘柄コード** に表示したい証券コードを入力（例: `7203`、複数行入力も可）
2. **基準日** で表示の終端日を指定
3. **遡る日数** でチャートに表示する営業日数を設定（1〜60日）

<br><br>

## ディレクトリ構成

```
.
├── app.py          # メインアプリ
├── data_j.xls      # TOPIX銘柄一覧（別途配置）
├── requirements.txt
└── README.md
```

<br><br>

## ライセンス

MIT
