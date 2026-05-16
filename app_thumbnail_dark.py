import io
import numpy as np, pandas as pd
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from matplotlib.transforms import blended_transform_factory
from matplotlib.ticker import MaxNLocator
import streamlit as st, yfinance as yf
from datetime import datetime, timedelta

DAYS, DPI = 30, 100
FIG_W, FIG_H = 12.80, 6.70
BG, FG, MUTED, GRID = "#0e1116", "#f3f4f6", "#9ca3af", "#1f2937"

_JP = next((f.name for f in fm.fontManager.ttflist
            if f.name in ("BIZ UDGothic","Yu Gothic","Meiryo","MS PGothic")), None)
if _JP: plt.rcParams["font.family"] = [_JP, "sans-serif"]


def fetch(code):
    end = datetime.today().date()
    df = yf.download(f"{code}.T",
                     start=(end - timedelta(days=DAYS)).isoformat(),
                     end=(end + timedelta(days=1)).isoformat(),
                     interval="5m", progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.dropna(subset=["Close"])
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None: df.index = df.index.tz_localize(None)
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
    ch = "#22c55e"
    cr = tuple(int(ch[j:j+2],16)/255 for j in (1,3,5))
    xs = np.arange(len(c), dtype=float)
    lo, hi = c.min(), c.max(); rng = hi-lo or 1
    ylo, yhi = lo-rng*.04, hi+rng*.04

    fig = plt.figure(figsize=(FIG_W,FIG_H), dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0.04,0.15,0.55,0.76]); ax.set_facecolor(BG)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(left=False,bottom=False,labelleft=False,labelbottom=False)
    ax.set_xlim(-0.5,len(c)-0.5); ax.set_ylim(ylo,yhi)

    vts = [(xs[0],c[0])]+list(zip(xs[1:],c[1:]))+[(xs[-1],ylo),(xs[0],ylo),(xs[0],c[0])]
    pcs = [MPath.MOVETO]+[MPath.LINETO]*(len(c)-1)+[MPath.LINETO,MPath.LINETO,MPath.CLOSEPOLY]
    clip = PathPatch(MPath(vts,pcs), transform=ax.transData, visible=False); ax.add_patch(clip)
    grad = np.zeros((256,2,4), dtype=np.float32)
    for i in range(256): grad[i] = [*cr, 0.55*(1-i/255)]
    im = ax.imshow(grad, aspect="auto", extent=[xs[0],xs[-1],ylo,hi],
                   origin="upper", zorder=1, interpolation="bilinear"); im.set_clip_path(clip)
    ax.plot(xs,c, color=ch, linewidth=2.6, zorder=2, solid_capstyle="round", solid_joinstyle="round")

    trans = blended_transform_factory(ax.transAxes, ax.transData)
    for yv in [t for t in MaxNLocator(nbins=4).tick_values(lo,hi) if lo<t<hi]:
        ax.axhline(yv, color=GRID, linewidth=.7, zorder=0)
        ax.text(0.01, yv, f"{yv:,.0f}", transform=trans, ha="left", va="bottom",
                fontsize=24, color=MUTED, zorder=3,
                bbox=dict(facecolor=BG, alpha=0.6, edgecolor="none", pad=2))

    dates = pd.DatetimeIndex(df.index); seen, last = {}, -0.15
    for xi,dt in enumerate(dates):
        if (k:=(dt.month,dt.day)) not in seen: seen[k] = xi
    for md, xi in sorted(seen.items()):
        xa = (xi+.5)/len(c)
        if xa>.93 or xa-last<.08: continue
        last = xa
        ax.plot([xa,xa], [0,-.025], transform=ax.transAxes, color=MUTED, linewidth=1., clip_on=False)
        ax.text(xa, -.045, f"{md[0]}/{md[1]}", transform=ax.transAxes, ha="left", va="top",
                fontsize=24, color=MUTED)

    ax2 = fig.add_axes([.62,.05,.36,.90]); ax2.set_facecolor(BG); ax2.axis("off")
    active = [l.strip() for l in lines if l.strip()]
    disp = [(p, i==0) for i,l in enumerate(active) for p in wrap_jp(l, 6 if i==0 else 10)]
    sf, so = .23, .11
    yp = .5 + sum(sf if f else so for _,f in disp)/2 - .02
    for txt, is_first in disp:
        ax2.text(.04, yp, txt, transform=ax2.transAxes,
                 fontsize=56 if is_first else 33, fontweight="bold" if is_first else "normal",
                 color=FG, va="top")
        yp -= sf if is_first else so

    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=DPI, facecolor=BG, bbox_inches=None)
    plt.close(fig); buf.seek(0); return buf.read()


if __name__ == "__main__":
    st.set_page_config(page_title="Chart Image", layout="centered")
    st.title("Chart Image Generator")
    c1, c2 = st.columns(2)
    code  = c1.text_input("Stock Code",  placeholder="e.g. 5020")
    texts = c2.text_area("Right-side text", height=130,
                         placeholder="e.g. ENEOS 5020\n14日決算発表後に急落も翌日反発")

    if st.button("Generate", type="primary", disabled=not code.strip()):
        with st.spinner("Fetching data..."): df, name = fetch(code.strip())
        if df.empty: st.error("Could not fetch data.")
        else:
            st.markdown(f"### {name} ({code})")
            img = render(df, code.strip(), name, texts.split("\n") if texts else [])
            st.image(img)
            st.download_button("Download PNG", data=img, file_name=f"chart_{code}.png",
                               mime="image/png", type="primary")
