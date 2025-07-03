import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from gridstatusio import GridStatusClient
import pandas as pd
import plotly.express as px

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ERCOT CP Load Live Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── HEADER WITH LOGO & CREDIT ───────────────────────────────────────────────
col1, col2 = st.columns([1.5, 8])
with col1:
    st.image(
        "https://www.nuenergen.com/wp-content/uploads/2022/08/NuEnergen-SVG.svg",
        width=180,  # bumped logo size
    )
with col2:
    st.markdown(
        """
        <h1 style="margin-bottom:0; color:#ffffff;">
          ⚡ ERCOT Estimated Coincident-Peak Load
        </h1>
        <p style="margin-top:0; color:#aaaaaa;">
          Last 2 Weeks • Live Dashboard
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <p style="text-align:right; font-size:0.8rem; color:#777777;">
          Built by <strong>Nicholas Yanoti</strong>, NuEnergen Intern
        </p>
        """,
        unsafe_allow_html=True,
    )

# ─── JS REFRESH SCHEDULER FOR :01, :16, :31, :46 ─────────────────────────────
components.html(
    """
    <script>
      (function() {
        const schedule = [1, 16, 31, 46];
        const now = new Date();
        let next = schedule.find(m => now.getMinutes() < m);
        if (next === undefined) next = schedule[0] + 60;
        let delta = (next - now.getMinutes()) * 60 - now.getSeconds();
        if (delta < 0) delta += 3600;
        setTimeout(() => window.location.reload(), delta * 1000);
      })();
    </script>
    """,
    height=0,
)

# ─── DATA FETCH (no cache between reloads) ────────────────────────────────────
@st.cache_data(ttl=0)
def fetch_ecp(days: int = 14) -> pd.DataFrame:
    client = GridStatusClient()  # reads $GRIDSTATUS_API_KEY
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    df = client.get_dataset(
        dataset="ercot_estimated_coincident_peak_load",
        start=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end=end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        timezone="market",
    )
    df["interval_start_local"] = pd.to_datetime(df["interval_start_local"])
    return df

df = fetch_ecp()

# ─── FOOTER INFO ──────────────────────────────────────────────────────────────
st.markdown(
    f"**Last updated (UTC):** {datetime.utcnow():%Y-%m-%d %H:%M:%SZ}  \n"
    f"**Next refresh at** :01, :16, :31, and :46 of each hour",
    unsafe_allow_html=True,
)

# ─── PLOTLY MULTI-LINE CHART ─────────────────────────────────────────────────
cols = [
    "operational_load",
    "internal_generation",
    "wholesale_storage_load",
    "net_dc_tie_flow",
    "dc_tie_exports",
    "dc_tie_imports",
    "estimated_cp_load",
    "estimated_cp_load_using_gen",
]

fig = px.line(
    df,
    x="interval_start_local",
    y=cols,
    labels={
        "interval_start_local": "Local Time",
        "value": "MW",
        "variable": "Series"
    },
    template="plotly_dark",
)

# Increase overall chart size, padding, and add fixed height
fig.update_layout(
    height=900,                 # explicitly set plot height
    hovermode="x unified",
    legend=dict(
        title="Series",
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(t=180, r=60, b=60, l=60)  # more top-padding for title & legend
)

# Render the chart full-width with extra vertical room
st.plotly_chart(fig, use_container_width=True, height=950)

# ─── RAW DATA EXPANDER ─────────────────────────────────────────────────────────
with st.expander("Show raw data"):
    st.dataframe(df.set_index("interval_start_local"), use_container_width=True)

# ─── HIDE STREAMLIT DEFAULT UI ────────────────────────────────────────────────
st.markdown(
    """
    <style>
      #MainMenu, footer, header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)
