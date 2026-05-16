import io
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import matplotlib.font_manager as fm

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# ── フォント選択 ───────────────────────────────────────────────
def _pick_jp_font() -> str:
    available = {f.name for f in fm.fontManager.ttflist}
    for candidate in ["BIZ UDGothic", "Yu Gothic", "Meiryo", "MS PGothic"]:
        if candidate in available:
            return candidate
    return matplotlib.rcParams["font.family"][0]

JP_FONT = _pick_jp_font()

# ── カラーパレット ─────────────────────────────────────────────
BG        = "#0e1116"
FG        = "#f3f4f6"
SUB       = "#9ca3af"
GRID_CLR  = "#1f2937"
LINE_CLR  = "#22c55e"

# ── データ取得 ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_data(code: str):
    ticker_sym = f"{code}.T"

    # 銘柄名
    try:
        name = yf.Search(ticker_sym, max_results=1).quotes[0]["shortname"]
    except Exception:
        name = code

    # 5分足 30日
    df = yf.download(ticker_sym, period="30d", interval="5m", progress=False)
    if df.empty:
        return None, name

    # MultiIndex 平坦化
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # タイムゾーン除去
    if df.index.tzinfo is not None:
        df.index = df.index.tz_localize(None)

    df = df[["Close"]].dropna()
    return df, name


# ── 日本語折り返し ─────────────────────────────────────────────
def wrap_jp(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=True)


# ── グラデーション塗り ────────────────────────────────────────
def _gradient_fill(ax, x, y, color_hex: str):
    """折れ線下にアルファグラデーション(上: 0.5 → 下: 0)を描画"""
    rgb = matplotlib.colors.to_rgb(color_hex)

    # グラデーション画像: shape (256, 2, 4) RGBA
    img_data = np.zeros((256, 2, 4))
    img_data[:, :, :3] = rgb
    img_data[:, :, 3] = np.linspace(0.5, 0.0, 256)[:, np.newaxis]

    xmin, xmax = x[0], x[-1]
    ymin = ax.get_ylim()[0]
    ymax = max(y)

    im = ax.imshow(
        img_data,
        aspect="auto",
        origin="upper",
        extent=[xmin, xmax, ymin, ymax],
        zorder=1,
    )

    # 折れ線の下領域でクリップ
    verts = [(xv, yv) for xv, yv in zip(x, y)]
    verts += [(x[-1], ymin), (x[0], ymin), (x[0], y[0])]
    codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 1)
    clip_path = PathPatch(Path(verts, codes), transform=ax.transData)
    ax.add_patch(clip_path)
    clip_path.set_visible(False)
    im.set_clip_path(clip_path)


# ── チャート描画 ─────────────────────────────────────────────
def _draw_chart(ax, df: pd.DataFrame):
    x = np.arange(len(df))
    y = df["Close"].values.astype(float)

    # グラデーション塗り（先に描く）
    ax.set_xlim(x[0], x[-1])
    pad = (y.max() - y.min()) * 0.1 or 1.0
    ax.set_ylim(y.min() - pad, y.max() + pad)
    _gradient_fill(ax, x, y, LINE_CLR)

    # 折れ線
    ax.plot(
        x, y,
        color=LINE_CLR,
        linewidth=2.6,
        solid_capstyle="round",
        zorder=3,
    )

    # 軸非表示
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False,
                   labelleft=False, labelbottom=False)

    # 水平グリッド + 価格ラベル
    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4))
    ax.grid(axis="y", color=GRID_CLR, linewidth=0.8, zorder=0)
    yticks = ax.get_yticks()
    ylim = ax.get_ylim()
    for yv in yticks:
        if ylim[0] < yv < ylim[1]:
            ax.text(
                x[0], yv,
                f" {yv:,.0f}",
                color=SUB,
                fontsize=24,
                fontfamily=JP_FONT,
                va="center",
                ha="left",
                zorder=4,
                bbox=dict(
                    boxstyle="round,pad=0.15",
                    facecolor=BG,
                    alpha=0.6,
                    edgecolor="none",
                ),
            )

    # 日付ラベル（チャート下端・全域カバー）
    df_dates = df.index.normalize()
    unique_dates = sorted(df_dates.unique())
    n_labels = min(5, len(unique_dates))
    date_indices = np.linspace(0, len(unique_dates) - 1, n_labels).astype(int)

    # blended transform: x=data座標, y=axes座標
    blended = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)

    for di in date_indices:
        target_date = unique_dates[di]
        # その日の最初のデータ点インデックス
        mask = df_dates == target_date
        first_idx = int(np.where(mask)[0][0])

        # 短い垂直ティック（axes座標で下方向）
        ax.plot(
            [first_idx, first_idx],
            [-0.025, 0.0],
            transform=blended,
            color=SUB,
            linewidth=1.2,
            clip_on=False,
            zorder=5,
        )

        # 日付ラベル
        label = f"{target_date.month}/{target_date.day}"
        ax.text(
            first_idx, -0.045,
            label,
            transform=blended,
            color=SUB,
            fontsize=22,
            fontfamily=JP_FONT,
            ha="left",
            va="top",
            clip_on=False,
            zorder=5,
        )


# ── テキストパネル描画 ─────────────────────────────────────────
def _draw_text_panel(ax, lines: list[str], name: str):
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False,
                   labelleft=False, labelbottom=False)

    if not lines:
        return

    # 1行目: 大見出し（6文字折り返し）
    headline_raw = lines[0]
    headline_lines = wrap_jp(headline_raw, width=6)

    # 2行目以降: 説明（10文字折り返し）
    body_lines_raw = lines[1:]
    body_lines = []
    for bl in body_lines_raw:
        body_lines.extend(wrap_jp(bl, width=10))

    # 銘柄名（上部に小さく）
    name_lines = wrap_jp(name, width=12)

    # 行数に応じた y 座標計算（上下中央）
    line_h_head = 0.13   # 見出し1行の高さ割合
    line_h_body = 0.08
    line_h_name = 0.05
    gap = 0.04           # 見出しと本文の間

    total_h = (
        len(name_lines) * line_h_name
        + 0.03
        + len(headline_lines) * line_h_head
        + (gap if body_lines else 0)
        + len(body_lines) * line_h_body
    )

    y_start = 0.5 + total_h / 2

    y = y_start

    # 銘柄名
    for nl in name_lines:
        ax.text(
            0.08, y, nl,
            color=SUB,
            fontsize=22,
            fontfamily=JP_FONT,
            fontweight="normal",
            va="top", ha="left",
            transform=ax.transAxes,
        )
        y -= line_h_name
    y -= 0.03

    # 見出し
    for hl in headline_lines:
        ax.text(
            0.08, y, hl,
            color=FG,
            fontsize=56,
            fontfamily=JP_FONT,
            fontweight="bold",
            va="top", ha="left",
            transform=ax.transAxes,
        )
        y -= line_h_head

    # 本文
    if body_lines:
        y -= gap
        for bl in body_lines:
            ax.text(
                0.08, y, bl,
                color=SUB,
                fontsize=33,
                fontfamily=JP_FONT,
                fontweight="normal",
                va="top", ha="left",
                transform=ax.transAxes,
            )
            y -= line_h_body


# ── 画像生成 ──────────────────────────────────────────────────
def generate_image(df: pd.DataFrame, name: str, user_text: str) -> bytes:
    W, H = 1280, 670
    dpi = 100
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi, facecolor=BG)

    # 左60% チャート
    ax_chart = fig.add_axes([0.02, 0.12, 0.56, 0.80])
    _draw_chart(ax_chart, df)

    # 縦区切り線
    fig.add_artist(
        plt.Line2D(
            [0.60, 0.60], [0.05, 0.95],
            transform=fig.transFigure,
            color=GRID_CLR,
            linewidth=1.0,
        )
    )

    # 右40% テキスト
    ax_text = fig.add_axes([0.61, 0.05, 0.38, 0.90])
    user_lines = [l for l in user_text.split("\n") if l.strip()]
    _draw_text_panel(ax_text, user_lines, name)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── Streamlit UI ──────────────────────────────────────────────
st.set_page_config(
    page_title="株価チャート画像ジェネレーター",
    page_icon="📈",
    layout="centered",
)

st.markdown(
    f"""
    <style>
    body, .stApp {{ background-color: {BG}; color: {FG}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📈 株価チャート画像ジェネレーター")
st.caption("東証銘柄コードを入力して SNS サムネイル用 PNG を生成します")

col1, col2 = st.columns([1, 2])

with col1:
    code = st.text_input(
        "銘柄コード（東証4桁）",
        value="5020",
        max_chars=6,
        placeholder="例: 5020",
    )

with col2:
    user_text = st.text_area(
        "右側に表示するテキスト（1行目=大見出し、2行目以降=説明）",
        value="増収増益\n営業利益 前年比+30%\n配当利回り 3.5%",
        height=120,
    )

if st.button("🚀 Generate", type="primary", use_container_width=True):
    if not code.strip():
        st.error("銘柄コードを入力してください")
    else:
        with st.spinner("データ取得中…"):
            df, name = fetch_data(code.strip())

        if df is None or df.empty:
            st.error(f"「{code}.T」のデータが取得できませんでした。銘柄コードをご確認ください。")
        else:
            with st.spinner("画像生成中…"):
                img_bytes = generate_image(df, name, user_text)

            st.success(f"✅ {name}（{code}.T）のチャート画像を生成しました")
            st.image(img_bytes, use_container_width=True)

            st.download_button(
                label="⬇️ PNG をダウンロード",
                data=img_bytes,
                file_name=f"chart_{code}.png",
                mime="image/png",
                use_container_width=True,
            )
