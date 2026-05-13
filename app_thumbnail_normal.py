import io
import numpy as np, pandas as pd
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from matplotlib.transforms import blended_transform_factory
import streamlit as st, yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Chart Image", layout="centered")

DAYS, DPI, TT, TB = 90, 100, 0.26, 0.10
FIG_W, FIG_H = 12.80, 6.70

_jp = next((f.name for f in fm.fontManager.ttflist
            if f.name in ("BIZ UDGothic","Yu Gothic","Meiryo","MS PGothic")), None)
if _jp: plt.rcParams["font.family"] = [_jp, "sans-serif"]


def fetch(code):
    end = datetime.today().date()
    df = yf.download(f"{code}.T",
                     start=(end - timedelta(days=DAYS + 40)).isoformat(),
                     end=(end + timedelta(days=1)).isoformat(),
                     interval="1d", progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.dropna(subset=["Close"])
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    last_price = None
    try:
        fi = yf.Ticker(f"{code}.T").fast_info
        last_price = float(fi.get("lastPrice") or fi.get("last_price") or 0) or None
    except Exception:
        pass

    if last_price:
        last_date = df.index[-1].date() if not df.empty else None
        today_ts  = pd.Timestamp(end)
        if last_date != end:
            row = pd.DataFrame({
                "Open": [last_price], "High": [last_price], "Low": [last_price],
                "Close": [last_price], "Volume": [0],
            }, index=[today_ts])
            df = pd.concat([df, row])
        else:
            df.loc[df.index[-1], "Close"] = last_price

    df = df.tail(DAYS)
    try:
        q = yf.Search(f"{code}.T", max_results=1).quotes if not df.empty else []
        name = (q[0].get("shortname") or code) if q else code
    except Exception: name = code
    return df, name


def wrap_jp(t, w):
    t = t.strip()
    return [t[i:i+w] for i in range(0, len(t), w)] if t else []


def render(df, code, name, lines):
    c = df["Close"].values.astype(float)
    up = c[-1] >= c[0]
    ch = "#16a34a" if up else "#dc2626"
    cr = tuple(int(ch[j:j+2],16)/255 for j in (1,3,5))
    xs = np.arange(len(c), dtype=float)
    lo, hi = c.min(), c.max(); rng = hi-lo or 1
    full = rng/(1-TT-TB); ylo, yhi = lo-full*TB, hi+full*TT

    fig = plt.figure(figsize=(FIG_W,FIG_H), dpi=DPI, facecolor="white")
    ax = fig.add_axes([0.04,0.05,0.55,0.90]); ax.set_facecolor("white")
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(left=False,bottom=False,labelleft=False,labelbottom=False)
    ax.set_xlim(-0.5,len(c)-0.5); ax.set_ylim(ylo,yhi)

    if "Volume" in df.columns:
        v = df["Volume"].fillna(0).values.astype(float); pv = v[v>0]
        if len(pv):
            vref = float(np.percentile(pv,95))
            ax.bar(xs, np.clip(v,0,vref)/vref*rng*.20, bottom=lo,
                   color=(.65,.65,.65,.35), width=1., zorder=1)

    vts = [(xs[0],c[0])]+list(zip(xs[1:],c[1:]))+[(xs[-1],lo),(xs[0],lo),(xs[0],c[0])]
    pcs = [MPath.MOVETO]+[MPath.LINETO]*(len(c)-1)+[MPath.LINETO,MPath.LINETO,MPath.CLOSEPOLY]
    clip = PathPatch(MPath(vts,pcs), transform=ax.transData, visible=False); ax.add_patch(clip)
    grad = np.zeros((256,2,4), dtype=np.float32)
    for i in range(256): grad[i] = [*cr, 0.40*(1-i/255)]
    im = ax.imshow(grad, aspect="auto", extent=[xs[0],xs[-1],lo,hi],
                   origin="upper", zorder=1, interpolation="bilinear"); im.set_clip_path(clip)
    ax.plot(xs,c, color=ch, linewidth=2.6, zorder=2, solid_capstyle="round", solid_joinstyle="round")

    trans = blended_transform_factory(ax.transAxes, ax.transData)
    ax.axhline(lo, color="#dadce0", linewidth=.8, zorder=0)
    for yv in np.linspace(lo,hi,5)[1:-1]:
        ax.axhline(yv, color="#eceff1", linewidth=.8, zorder=0)
        ax.text(0.01, yv, f"{yv:,.0f}", transform=trans, ha="left", va="bottom",
                fontsize=16, color="#5f6368", zorder=3,
                bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=2))

    dates = pd.DatetimeIndex(df.index); seen, last = {}, -0.15
    for xi,dt in enumerate(dates):
        if (k:=(dt.year,dt.month)) not in seen: seen[k] = xi
    for ym, xi in sorted(seen.items()):
        xa = (xi+.5)/len(c)
        if xa>.93 or xa-last<.08: continue
        last = xa
        ax.plot([xa,xa],[TB,TB-.014], transform=ax.transAxes,
                color="#80868b", linewidth=1., clip_on=False)
        ax.text(xa, TB-.020, f"{ym[1]}月", transform=ax.transAxes,
                ha="left", va="top", fontsize=16, color="#5f6368")

    chg = (c[-1]/c[-2]-1)*100 if len(c)>1 else 0
    ar = "↑" if chg>0 else ("↓" if chg<0 else "→"); sg = "+" if chg>0 else ""
    ax.text(.02,.985, name, transform=ax.transAxes, fontsize=24, fontweight="bold", color="#202124", va="top")
    ax.text(.99,.985, code, transform=ax.transAxes, fontsize=16, fontweight="bold", color="#5f6368", va="top", ha="right")
    _last = c[-1]; _last_str = f"{_last:,.1f}" if _last != int(_last) else f"{int(_last):,}"
    ax.text(.02,.880, f"{_last_str}円", transform=ax.transAxes, fontsize=22, fontweight="bold", color="#202124", va="top")
    ax.text(.02,.770, f"{ar} {sg}{chg:.2f}%", transform=ax.transAxes, fontsize=16, fontweight="bold", color=ch, va="top")
    ax.text(.22,.772, f"({DAYS}日)", transform=ax.transAxes, fontsize=16, color="#80868b", va="top")

    ax2 = fig.add_axes([.62,.05,.36,.90]); ax2.set_facecolor("white"); ax2.axis("off")
    active = [l.strip() for l in lines if l.strip()]
    disp = [(p, i==0) for i,l in enumerate(active) for p in wrap_jp(l, 9 if i==0 else 13)]
    sf, so = .135, .075
    yp = .5 + sum(sf if f else so for _,f in disp)/2 - .02
    for txt, is_first in disp:
        ax2.text(.04, yp, txt, transform=ax2.transAxes,
                 fontsize=32 if is_first else 22, fontweight="bold" if is_first else "normal",
                 color="#202124", va="top")
        yp -= sf if is_first else so

    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=DPI, facecolor="white", bbox_inches=None)
    plt.close(fig); buf.seek(0); return buf.read()


st.title("Chart Image Generator")
c1, c2 = st.columns(2)
code  = c1.text_input("Stock Code", value="8053", placeholder="e.g. 7203")
texts = c2.text_area("Right-side text", height=130,
                     placeholder="住友商 8053\n決算後に急伸、株式分割と自社株消却を発表")

if st.button("Generate", type="primary", disabled=not code.strip()):
    with st.spinner("Fetching data..."): df, name = fetch(code.strip())
    if df.empty: st.error("Could not fetch data.")
    else:
        img = render(df, code.strip(), name, texts.split("\n") if texts else [])
        st.image(img)
        st.download_button("Download PNG", data=img, file_name=f"chart_{code}.png",
                           mime="image/png", type="primary")
