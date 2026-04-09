def score_tracker_page():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from datetime import datetime, timedelta
    import pytz

    PERU_TZ = pytz.timezone("America/Lima")

    st.title("\U0001f3af Portfolio Score Tracker")
    st.caption("\u05de\u05e2\u05e7\u05d1 \u05e6\u05d9\u05d5\u05df + \u05de\u05d3\u05d3\u05d9\u05dd \u05dc\u05d0\u05d7\u05e8 \u05d9\u05d5\u05dd \u05d4\u05db\u05e0\u05d9\u05e1\u05d4 \u05dc\u05e4\u05d5\u05e8\u05d8\u05e4\u05d5\u05dc\u05d9\u05d5 \u2014 3 \u05d9\u05de\u05d9 \u05de\u05e1\u05d7\u05e8, \u05d3\u05e7\u05d4 \u05d0\u05d7\u05e8 \u05d3\u05e7\u05d4")
    system_health_bar()

    def trading_days_after(sd, n=3):
        d = datetime.strptime(sd, "%Y-%m-%d")
        days = []
        while len(days) < n:
            d += timedelta(days=1)
            if d.weekday() < 5:
                days.append(d.strftime("%Y-%m-%d"))
        return days

    @st.cache_data(ttl=60)
    def load_data():
        try:
            from gsheets_sync import _get_client, SPREADSHEET_ID
            gc = _get_client()
            if gc is None: return pd.DataFrame(), pd.DataFrame()
            sh = gc.open_by_key(SPREADSHEET_ID)
            today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

            # Load portfolio — find active stocks
            port = sh.worksheet("portfolio").get_all_values()
            port_df = pd.DataFrame(port[1:], columns=port[0]) if len(port) > 1 else pd.DataFrame()
            active = []
            if not port_df.empty:
                for r in port_df.itertuples():
                    sd = str(r.Date).strip()
                    _d = datetime.strptime(today, "%Y-%m-%d")
                    while True:
                        _d -= timedelta(days=1)
                        if _d.weekday() < 5:
                            _prev = _d.strftime("%Y-%m-%d")
                            break
                    if sd and sd == _prev:
                        active.append({"Ticker": r.Ticker, "ScanDate": sd, "EntryScore": r.Score, "EntryPrice": r.BuyPrice})
            active_df = pd.DataFrame(active).drop_duplicates(["Ticker","ScanDate"]) if active else pd.DataFrame()

            # Load score_tracker data
            try:
                ws = sh.worksheet("score_tracker")
                data = ws.get_all_values()
                tracker_df = pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()
                for col in ["Score","Price","MxV","RunUp","RSI","ATRX","REL_VOL","Gap","VWAP"]:
                    if col in tracker_df.columns:
                        tracker_df[col] = pd.to_numeric(tracker_df[col], errors="coerce")
            except:
                tracker_df = pd.DataFrame()

            return active_df, tracker_df
        except Exception as e:
            st.error(f"Error: {e}")
            return pd.DataFrame(), pd.DataFrame()

    with st.spinner("Loading..."):
        active_df, tracker_df = load_data()

    today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

    # Always show active stocks table
    st.subheader(f"\U0001f4cb Active stocks today ({today})")
    if active_df.empty:
        st.info("No active portfolio stocks for tracking today.")
    else:
        st.dataframe(active_df, use_container_width=True, hide_index=True)
        if tracker_df.empty:
            st.warning(f"\u23f3 Waiting for market open (08:30 Peru) — {len(active_df)} stocks will be tracked")
        else:
            today_rows = tracker_df[tracker_df["Date"] == today]
            st.success(f"\u2705 {len(today_rows)} rows collected today so far")

    if tracker_df.empty:
        return

    st.divider()

    with st.sidebar:
        st.header("\U0001f3af Portfolio Score Tracker")
        pairs = sorted(set(
            f"{r.Ticker} ({r.ScanDate})"
            for r in tracker_df.drop_duplicates(["Ticker","ScanDate"]).itertuples()
        ), reverse=True)
        if not pairs:
            return
        selected = st.selectbox("Select stock", pairs)
        if not selected: return
        ticker = selected.split(" (")[0]
        scan_date = selected.split("(")[1].rstrip(")")
        show_metrics = st.multiselect(
            "Metrics", ["MxV","RunUp","RSI","ATRX","REL_VOL","Gap","VWAP"],
            default=["MxV","ATRX","REL_VOL"]
        )

    sdf = tracker_df[(tracker_df["Ticker"]==ticker)&(tracker_df["ScanDate"]==scan_date)].copy()
    sdf = sdf.sort_values(["Date","ScanTime"])
    sdf["DateTime"] = pd.to_datetime(sdf["Date"]+" "+sdf["ScanTime"], errors="coerce")
    if sdf.empty:
        st.warning("No data yet for this stock"); return

    days = sorted(sdf["Date"].unique())
    first_s = sdf["Score"].iloc[0]
    last_s  = sdf["Score"].iloc[-1]
    delta_s = last_s - first_s

    st.subheader(f"\U0001f4c8 {ticker} — Entry {scan_date}")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Entry Score", f"{first_s:.2f}")
    c2.metric("Current Score", f"{last_s:.2f}", f"{delta_s:+.2f}")
    c3.metric("Max", f"{sdf['Score'].max():.2f}")
    c4.metric("Min", f"{sdf['Score'].min():.2f}")
    c5.metric("Days", len(days))
    st.divider()

    COLORS = ["#00d4ff","#ff6b35","#7fff7f","#ff88cc"]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
        subplot_titles=("Score over time","Price"),
        row_heights=[0.6,0.4], vertical_spacing=0.12)
    for i,day in enumerate(days):
        dd = sdf[sdf["Date"]==day]
        c = COLORS[i%4]
        lbl = f"D{i+1} ({day})"
        fig.add_trace(go.Scatter(x=dd["DateTime"],y=dd["Score"],mode="lines",
            name=lbl,line=dict(color=c,width=2)),row=1,col=1)
        fig.add_trace(go.Scatter(x=dd["DateTime"],y=dd["Price"],mode="lines",
            name=lbl,line=dict(color=c,width=1.5,dash="dot"),showlegend=False),row=2,col=1)
    fig.add_hline(y=60,line_dash="dash",line_color="#ff4444",opacity=0.5,annotation_text="Score 60",row=1,col=1)
    fig.update_layout(height=550,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0.1)",
        font=dict(color="#cccccc"),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
        margin=dict(l=40,r=40,t=60,b=40))
    fig.update_xaxes(showgrid=False,color="#888888")
    fig.update_yaxes(showgrid=True,gridcolor="rgba(255,255,255,0.05)",color="#888888")
    st.plotly_chart(fig, use_container_width=True)

    if show_metrics:
        mc = {"MxV":"#ff6b35","RunUp":"#00d4ff","RSI":"#ffdd57","ATRX":"#7fff7f","REL_VOL":"#ff88cc","Gap":"#b388ff","VWAP":"#80deea"}
        avail = [m for m in show_metrics if m in sdf.columns and sdf[m].notna().any()]
        if avail:
            st.subheader("Metrics breakdown")
            fig2 = go.Figure()
            for m in avail:
                for i,day in enumerate(days):
                    dd = sdf[sdf["Date"]==day]
                    fig2.add_trace(go.Scatter(x=dd["DateTime"],y=dd[m],mode="lines",
                        name=f"{m} D{i+1}",line=dict(color=mc.get(m,"#aaa"),width=1.5,dash=["solid","dot","dash","dashdot"][i%4])))
            fig2.update_layout(height=350,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0.1)",
                font=dict(color="#cccccc"),legend=dict(orientation="h",yanchor="bottom",y=1.02),margin=dict(l=40,r=40,t=40,b=40))
            fig2.update_xaxes(showgrid=False,color="#888888")
            fig2.update_yaxes(showgrid=True,gridcolor="rgba(255,255,255,0.05)",color="#888888")
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    with st.expander("Raw data"):
        scols = ["Date","ScanTime","Price","Score"]+[m for m in ["MxV","RunUp","RSI","ATRX","REL_VOL","Gap","VWAP"] if m in sdf.columns]
        st.dataframe(sdf[scols].style.format({c:"{:.2f}" for c in scols if c not in ["Date","ScanTime"]}),
            height=400,use_container_width=True)

