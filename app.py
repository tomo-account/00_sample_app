import streamlit as st
import pandas as pd
import altair as alt
import yfinance as yf
from datetime import datetime, timedelta, time
from time import sleep
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
Y = 50

@st.cache_resource(show_spinner=False)
def load_topix():
    try:
        df = pd.read_excel(BASE_DIR / "data_j.xls")
        return dict(zip(df['コード'].astype(str), df['銘柄名']))
    except:
        return {}

@st.cache_data(ttl=300)
def load_stock(code, end_dt, days):
    sym = f"{code}.T"
    df5 = yf.download(sym, start=end_dt - timedelta(days=45),
                      end=end_dt + timedelta(days=1), interval="5m", progress=False)
    dfd = yf.download(sym, start=end_dt - timedelta(days=180),
                      end=end_dt + timedelta(days=1), interval="1d", progress=False)
    if df5.empty or dfd.empty:
        return pd.DataFrame(), pd.DataFrame()
    for d in [df5, dfd]:
        if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    df5 = df5.reset_index()
    df5['Datetime'] = pd.to_datetime(df5.get('Datetime', df5.get('Date'))).dt.tz_convert('Asia/Tokyo')
    dates = sorted(df5['Datetime'].dt.date.unique(), reverse=True)[:days]
    dfd.index = pd.to_datetime(dfd.index).date
    return df5[df5['Datetime'].dt.date.isin(dates)].sort_values('Datetime'), dfd

def daily_line_chart(dfd):
    df = dfd.reset_index().rename(columns={'index': 'Date'})[['Date', 'Close']]
    return alt.Chart(df).mark_line(color='#FF4B4B', strokeWidth=1.5).encode(
        x=alt.X('Date:T', title=None, axis=alt.Axis(format='%m月', grid=False)),
        y=alt.Y('Close:Q', title=None, scale=alt.Scale(zero=False), axis=alt.Axis(minExtent=Y)),
        tooltip=['Date', 'Close']
    ).properties(height=200)

def candle_chart(df5):
    df = df5.copy()
    df['x']    = df['Datetime'].dt.strftime('%y/%m/%d %H:%M')
    df['Vk']   = df['Volume'] / 1000
    df['date'] = df['Datetime'].dt.date
    df['is_am'] = df['Datetime'] == df.groupby('date')['Datetime'].transform('min')
    df['is_pm'] = df['Datetime'].dt.time == time(12, 30)
    ticks  = df[df['is_am'] | df['is_pm']]['x'].unique().tolist()
    lo, hi = df['Close'].min(), df['Close'].max()
    yscale = alt.Scale(domain=[float(lo - (hi-lo)*.05), float(hi + (hi-lo)*.05)], zero=False)
    color  = alt.condition("datum.Open <= datum.Close", alt.value("#ef5350"), alt.value("#26a69a"))
    base   = alt.Chart(df).encode(
        x=alt.X('x:O', sort=None, axis=alt.Axis(labels=False, values=ticks, grid=False, title=None))
    )
    rule = lambda d, c: alt.Chart(d).mark_rule(color=c).encode(x='x:O')
    candle = alt.layer(
        rule(df[df['is_am']], '#CCCCCC'), rule(df[df['is_pm']], '#EEEEEE'),
        base.mark_rule().encode(y=alt.Y('Low:Q', scale=yscale, axis=alt.Axis(minExtent=Y, title=None)), y2='High:Q', color=color),
        base.mark_bar().encode(y='Open:Q', y2='Close:Q', color=color)
    )
    volume = base.mark_bar(opacity=0.5).encode(
        y=alt.Y('Vk:Q', axis=alt.Axis(orient='left', minExtent=Y, title=None)), color=color
    ).properties(height=80)
    return alt.vconcat(candle, volume).resolve_scale(x='shared').configure_view(strokeOpacity=0)

def render(ticker, df5, dfd, name):
    c1, _, c3 = st.columns([2, 1, 1])
    with c1:
        st.subheader(f"{ticker} {name}")
        st.caption(f"📈 Max: {df5['High'].max():,.1f} JPY　　📉 Min: {df5['Low'].min():,.1f} JPY")
    with c3:
        st.altair_chart(daily_line_chart(dfd), width='stretch')
    s = df5.groupby(df5['Datetime'].dt.date).agg(
        Open=('Open','first'), High=('High','max'), Low=('Low','min'), Close=('Close','last')
    ).sort_index()
    idx = s.index.intersection(dfd.index)
    if len(idx): s.loc[idx, ['Open','High','Low','Close']] = dfd.loc[idx, ['Open','High','Low','Close']].values
    prev = dfd['Close'].shift(1)
    def chg_str(d):
        if d in prev.index and pd.notna(prev.loc[d]):
            v = (s.loc[d, 'Close'] - prev.loc[d]) / prev.loc[d] * 100
            return f"{'🔴' if v > 0 else '🟢' if v < 0 else ''}{v:+.2f}%"
        return "-"
    s['騰落率'] = [chg_str(d) for d in s.index]
    st.altair_chart(candle_chart(df5), width='stretch')
    tbl = s[['騰落率', 'Close']].rename(columns={'Close': '終値'})
    tbl.index = [d.strftime('%m/%d') for d in tbl.index]
    tbl['終値'] = tbl['終値'].apply(lambda x: f"{x:,.1f}" if isinstance(x, (int, float)) else x)
    st.dataframe(tbl.T, width='stretch')

st.set_page_config(page_title="５分足チャート", page_icon="📈", layout="wide")
st.markdown("<style>.stDataFrame div{border-radius:0px;}</style>", unsafe_allow_html=True)
st.sidebar.markdown("## 📈 ５分足チャート")

raw      = st.sidebar.text_area("銘柄コード", value="7203", height=160)
end_date = st.sidebar.date_input("基準日", value=datetime.now())
days     = st.sidebar.number_input("遡る日数", min_value=1, max_value=60, value=20, step=1)
tickers  = [t.strip() for t in re.split(r'[,\s\n]+', raw) if t.strip()]
topix    = load_topix()

for ticker in tickers:
    sleep(0.2)
    df5, dfd = load_stock(ticker, end_date, days)
    if not df5.empty:
        render(ticker, df5, dfd, topix.get(str(ticker), f"{ticker}.T"))