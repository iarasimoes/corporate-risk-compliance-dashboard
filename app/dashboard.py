import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.scoring.calculate_scores import calculate_company_score
from src.alerts.generate_alerts import generate_alerts
from src.processing.score_over_time import calculate_score_over_time
from src.insights.generate_insights import generate_insights
from src.ingestion.news_rss_collector import collect_all_news


st.set_page_config(
    page_title="Corporate Risk Dashboard",
    layout="wide"
)


def load_data():
    events_df = pd.read_csv("data/mock/events.csv")

    try:
        news_df = pd.read_csv("data/mock/news_events.csv")
        df = pd.concat([events_df, news_df], ignore_index=True)
    except FileNotFoundError:
        df = events_df

    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    df["severity"] = pd.to_numeric(df["severity"], errors="coerce").fillna(0)

    return df


def calculate_category_scores(df):
    if df.empty:
        return pd.DataFrame(columns=["risk_category", "severity", "company"])

    result = []

    for company in df["company"].unique():
        company_df = df[df["company"] == company]

        category_scores = (
            company_df
            .groupby("risk_category")["severity"]
            .sum()
            .reset_index()
        )

        category_scores["company"] = company
        result.append(category_scores)

    return pd.concat(result, ignore_index=True)


def calculate_radar_scores(df):
    if df.empty:
        return pd.DataFrame()

    radar_df = (
        df.groupby(["company", "risk_category"])["severity"]
        .sum()
        .reset_index()
    )

    return radar_df

def get_status(score):
    if score < 30:
        return "🟢 Normal"
    elif score < 55:
        return "🟡 Attention"
    elif score < 75:
        return "🟠 High Risk"
    else:
        return "🔴 Critical"


# =========================
# HEADER
# =========================

st.title("📊 Corporate Risk & Compliance Dashboard")
st.caption("Monitoring public signals of corporate distress and risk escalation")


# =========================
# DATA
# =========================

df = load_data()

company_options = ["All Companies"] + sorted(df["company"].dropna().unique().tolist())

st.sidebar.title("⚙️ Controls")

selected_company = st.sidebar.selectbox(
    "Select Company",
    company_options
)

if selected_company != "All Companies":
    filtered_df = df[df["company"] == selected_company]
else:
    filtered_df = df


# =========================
# SIDEBAR DATA CONTROLS
# =========================

st.sidebar.subheader("Data Controls")

companies = df["company"].dropna().unique().tolist()

if st.sidebar.button("🔄 Update News RSS"):
    with st.spinner("Fetching latest news..."):
        collect_all_news(companies)
    st.sidebar.success("News updated.")
    st.rerun()


# =========================
# SCORES
# =========================

scores = calculate_company_score(filtered_df)

st.subheader("📌 Key Risk Indicators")

if scores:
    cols = st.columns(len(scores))

    for i, (company, score) in enumerate(scores.items()):
        with cols[i]:
            st.metric(
                label=company,
                value=f"{score}",
                delta=get_status(score)
            )
else:
    st.info("No data available for the selected filter.")


# =========================
# INSIGHTS
# =========================

st.subheader("🧠 Risk Insights")

insights = generate_insights(filtered_df, scores)

if insights:
    for company, text in insights.items():
        with st.container():
            st.markdown(f"### {company}")
            st.markdown(text)
            st.divider()
else:
    st.info("No insights available.")


# =========================
# CHARTS
# =========================

col1, col2 = st.columns(2)

with col1:
    st.subheader("Risk Breakdown by Category")

    category_df = calculate_category_scores(filtered_df)

    if not category_df.empty:
        fig_category = px.bar(
            category_df,
            x="risk_category",
            y="severity",
            color="company",
            barmode="group",
            title="Risk Distribution per Category"
        )

        st.plotly_chart(fig_category, use_container_width=True)
    else:
        st.info("No category data available.")

with col2:
    st.subheader("Event Volume Over Time")

    events_over_time = (
        filtered_df
        .dropna(subset=["event_date"])
        .groupby("event_date")
        .size()
        .reset_index(name="event_count")
    )

    if not events_over_time.empty:
        fig_events = px.line(
            events_over_time,
            x="event_date",
            y="event_count",
            markers=True,
            title="Risk Events Over Time"
        )

        st.plotly_chart(fig_events, use_container_width=True)
    else:
        st.info("No event timeline available.")

st.subheader("🕸️ Risk Profile Radar")

radar_df = calculate_radar_scores(filtered_df)

if not radar_df.empty:
    fig_radar = px.line_polar(
        radar_df,
        r="severity",
        theta="risk_category",
        color="company",
        line_close=True,
        title="Risk Profile by Dimension"
    )

    st.plotly_chart(fig_radar, use_container_width=True)
else:
    st.info("No radar data available.")

# =========================
# RISK SCORE EVOLUTION
# =========================

st.subheader("📈 Risk Score Evolution")

score_timeline = calculate_score_over_time(filtered_df)

if not score_timeline.empty:
    fig_score = px.line(
        score_timeline,
        x="event_date",
        y="risk_score",
        color="company",
        markers=True,
        title="Risk Score Evolution Over Time"
    )

    st.plotly_chart(fig_score, use_container_width=True)
else:
    st.info("No score evolution available.")


# =========================
# ALERTS
# =========================

st.subheader("🚨 Generated Alerts")

alerts = generate_alerts(scores, filtered_df)

if alerts:
    for alert in alerts:
        if alert["severity"] == "Critical":
            st.error(f"🔴 {alert['company']}: {alert['message']}")
        elif alert["severity"] == "High":
            st.warning(f"🟠 {alert['company']}: {alert['message']}")
        else:
            st.info(f"🟡 {alert['company']}: {alert['message']}")
else:
    st.success("No alerts generated.")


# =========================
# EVENT LOG
# =========================

st.subheader("📋 Event Log")

st.dataframe(
    filtered_df.sort_values(by="event_date", ascending=False),
    use_container_width=True,
    height=350
)