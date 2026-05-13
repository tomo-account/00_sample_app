import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Prompt Builder", layout="centered")


def fetch_stock(code: str):
    try:
        end = datetime.today().date()
        df = yf.download(f"{code}.T",
                         start=(end - timedelta(days=400)).isoformat(),
                         end=(end + timedelta(days=1)).isoformat(),
                         interval="1d", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close"])
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        if df.empty:
            return None, None

        last_price = None
        try:
            fi = yf.Ticker(f"{code}.T").fast_info
            last_price = float(fi.get("lastPrice") or fi.get("last_price") or 0) or None
        except Exception:
            pass

        if last_price:
            last_date = df.index[-1].date()
            today_ts  = pd.Timestamp(end)
            if last_date != end:
                row = pd.DataFrame({
                    "Open": [last_price], "High": [last_price], "Low": [last_price],
                    "Close": [last_price], "Volume": [0],
                }, index=[today_ts])
                df = pd.concat([df, row])
            else:
                df.loc[df.index[-1], "Close"] = last_price

        q = yf.Search(f"{code}.T", max_results=1).quotes
        return df, ((q[0].get("shortname") or code) if q else code)
    except Exception:
        return None, None


def compute_indicators(df: pd.DataFrame) -> dict:
    c, v, n = df["Close"], df.get("Volume"), len(df)
    last = float(c.iloc[-1])
    x: dict = {"latest": last}

    for lab, d in [("1d", 1), ("5d", 5), ("20d", 20), ("60d", 60)]:
        if n > d:
            x[f"chg_{lab}"] = (last / float(c.iloc[-(d + 1)]) - 1) * 100

    for w in (25, 75):
        if n >= w:
            sma = float(c.rolling(w).mean().iloc[-1])
            x[f"sma{w}"], x[f"sma{w}_dev"] = sma, (last / sma - 1) * 100
            if w == 25:
                s = float(c.rolling(25).std().iloc[-1])
                x["bb_up"], x["bb_lo"] = sma + 2 * s, sma - 2 * s

    if n >= 15:
        d = c.diff()
        g = d.clip(lower=0).ewm(alpha=1/14, adjust=False).mean().iloc[-1]
        l = (-d.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean().iloc[-1]
        x["rsi14"] = 100 - 100 / (1 + g / l) if l > 0 else 100.0

    if n >= 26:
        m = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        s = m.ewm(span=9, adjust=False).mean()
        x["macd"], x["macd_sig"], x["macd_h"] = float(m.iloc[-1]), float(s.iloc[-1]), float((m - s).iloc[-1])

    if n >= 14:
        hi, lo = df.get("High", c), df.get("Low", c)
        tr = pd.concat([hi - lo, (hi - c.shift()).abs(), (lo - c.shift()).abs()], axis=1).max(axis=1)
        x["atr14"] = float(tr.ewm(span=14, adjust=False).mean().iloc[-1])

    win = c.iloc[-252:] if n >= 252 else c
    x["hi52"], x["lo52"] = float(win.max()), float(win.min())
    x["dev_hi52"], x["dev_lo52"] = (last / x["hi52"] - 1) * 100, (last / x["lo52"] - 1) * 100

    if v is not None and len(v) >= 6:
        vn, va = float(v.iloc[-1]), float(v.iloc[-6:-1].mean())
        x["vol"], x["vol_r"] = vn, (vn / va if va > 0 else None)
    return x


def format_indicators(code: str, name: str, x: dict) -> str:
    L = [f"銘柄: {name} ({code})", f"終値: {x['latest']:,.0f}円"]
    t = [f"{lab} {x[k]:+.2f}%" for lab, k in
         [("前日比", "chg_1d"), ("1週", "chg_5d"), ("1ヶ月", "chg_20d"), ("3ヶ月", "chg_60d")] if k in x]
    if t: L.append("騰落率: " + " / ".join(t))
    sma = [f"SMA{w} {x[f'sma{w}']:,.0f}円（乖離 {x[f'sma{w}_dev']:+.1f}%）" for w in (25, 75) if f"sma{w}" in x]
    if sma: L.append("移動平均: " + " / ".join(sma))
    if "bb_up" in x: L.append(f"BB(25): 上限{x['bb_up']:,.0f} / 下限{x['bb_lo']:,.0f}円")
    if "rsi14" in x:
        r = x["rsi14"]
        L.append(f"RSI14: {r:.1f}" + ("  → 売られ過ぎ圏" if r < 30 else "  → 買われ過ぎ圏" if r > 70 else ""))
    if "macd" in x:
        h = x["macd_h"]
        L.append(f"MACD: {x['macd']:.2f} / シグナル: {x['macd_sig']:.2f} / ヒスト: {h:.2f} → {'上昇' if h > 0 else '下降'}モメンタム")
    if "atr14" in x: L.append(f"ATR14: {x['atr14']:.2f}")
    L.append(f"52週高値: {x['hi52']:,.0f}円（乖離 {x['dev_hi52']:+.1f}%） / 52週安値: {x['lo52']:,.0f}円（乖離 {x['dev_lo52']:+.1f}%）")
    if x.get("vol_r"): L.append(f"出来高: {x['vol']:,.0f}株（5日平均比 ×{x['vol_r']:.2f}）")
    return "\n".join(L)


PROMPT_TEMPLATE = """提供された素材データを踏まえ、**X投稿を3パターン**作成してください。

## ペルソナ：株クラ匿名垢（インフルエンサー）
X（旧Twitter）で活動する中〜上級の匿名株クラスタ。
- 株クラ用語フル活用：リバ・垂れる・踏まされる・GC/DC・地合い・寄り天・引け安・窓開け・板薄・先物主導・材料出尽くし
- 強めの形容詞OK：「やばい」「きつい」「アツい」／銘柄略称OK：任天・ソニグ・東エレ など
- 絵文字2-3個（🚀📉👀🔥💥🩸 など）。**数字の直後**に置くと映える（「-11%🩸」）。末尾に #日本株 など1-2個

## 語り口：です調 × X投稿のリズム
基本「〜です」「〜ます」「〜と考えられます」。ただし全文を「です」で締めるとブログ調になります。X投稿らしさのコツ：
- **体言止めを混ぜる**：「売られ過ぎ圏🩸」「決算控えで様子見ムードです」
- **改行でリズム**：1文1〜2行、ブロック間に空行を入れる
- **冒頭インパクト**：銘柄名・数字・絵文字から入る（例「ENEOS、4週で-11%。」）
- **短文の連打**：長文1個より短文2〜3個
- **問いかけで締める**：「ここは押し目でしょうか、それともデッドキャットか…」
- NG：「〜だ／〜である」（硬い）／「〜だよ／〜じゃん」（カジュアル過ぎ）／「〜ですよね／〜ですね」（女性寄り）

## 視点：短期（直近20営業日）の3パターン切り口
- パターン1: 直近20日の流れを1文で言い切る（インパクト重視）
- パターン2: 期間中に効いた／効かなかったテーマを示す（考察・深掘り）
- パターン3: 今後20日程度の中期見どころをまとめる（フォワードルッキング）

## ステップ0：各パターンのテーゼを決める（本文を書く前に必ず実行）
3パターンそれぞれの核心メッセージを1行で決める。テーゼは「読者がリツイートしたくなる、示唆に富む命題」。

## ニュース・注目点
{theme}{ctx}

## 制約
- 各投稿は約140字以内
- データに無い数字・銘柄・イベントを事実として書かない（推測は「〜の可能性があります」と明示）
- 投資勧誘・断定的推奨（「買うべき」「必ず上がる」）は厳禁
- 数字は具体的に（「大きく上昇」より「+2.3%」）
- 事実の羅列にせず「だから何か（含意）」を必ず示す

## 出力形式
【パターン1】（本文）

【パターン2】（本文）

【パターン3】（本文）"""


# ── UI ───────────────────────────────────────────────────────────
st.title("Prompt Builder")
st.caption("株クラインフルエンサー × ～です調 × 短期視点（直近20営業日）")

code  = st.text_input("銘柄コード（任意）", placeholder="例: 5020  ← テクニカル指標を自動追加")
theme = st.text_area("ニュース・注目点", height=120,
                     placeholder="例: 決算後に急伸、株式分割と自社株消却を発表")

if st.button("プロンプトを作成", type="primary"):
    block = ""
    if code.strip():
        with st.spinner("株価データ取得中..."):
            df, name = fetch_stock(code.strip())
        if df is None or df.empty:
            st.warning("株価データを取得できませんでした。")
        else:
            block = format_indicators(code.strip(), name, compute_indicators(df))
    ctx = f"\n\n【テクニカル指標】\n{block}" if block else ""
    st.divider()
    st.subheader("生成プロンプト")
    st.text_area("", value=PROMPT_TEMPLATE.format(theme=theme or "(テーマ未入力)", ctx=ctx),
                 height=420, key="prompt_out", label_visibility="collapsed")
