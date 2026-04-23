import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd
from src.scoring.calculate_scores import calculate_company_score
import plotly.express as px
from src.alerts.generate_alerts import generate_alerts
from src.processing.score_over_time import calculate_score_over_time
from src.insights.generate_insights import generate_insights

st.set_page_config(page_title="Corporate Risk Dashboard", layout="wide")

st.title("Corporate Risk & Compliance Dashboard")

events_df = pd.read_csv("data/mock/events.csv")

try:
    news_df = pd.read_csv("data/mock/news_events.csv")
    df = pd.concat([events_df, news_df], ignore_index=True)
except FileNotFoundError:
    df = events_df

df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
df["event_date"] = pd.to_datetime(df["event_date"])

scores = calculate_company_score(df)

company_options = ["All Companies"] + sorted(df["company"].unique().tolist())

selected_company = st.sidebar.selectbox(
    "Select a company",
    company_options
)

if selected_company != "All Companies":
    filtered_df = df[df["company"] == selected_company]
else:
    filtered_df = df


st.subheader("Risk Score Overview")

cols = st.columns(len(scores))

for i, (company, score) in enumerate(scores.items()):
    with cols[i]:
        if score < 30:
            status = "🟢 Normal"
        elif score < 55:
            status = "🟡 Attention"
        elif score < 75:
            status = "🟠 High Risk"
        else:
            status = "🔴 Critical"

        st.metric(company, score, status)

st.subheader("Events Timeline")

st.dataframe(
    filtered_df.sort_values(by="event_date", ascending=False),
    use_container_width=True
)

def calculate_category_scores(df):
    result = []

    for company in df['company'].unique():
        company_df = df[df['company'] == company]

        category_scores = (
            company_df.groupby('risk_category')['severity']
            .sum()
            .reset_index()
        )

        category_scores['company'] = company
        result.append(category_scores)

    return pd.concat(result)

st.subheader("Risk Insights")

insights = generate_insights(filtered_df, scores)

for company, text in insights.items():
    st.info(f"{company}: {text}")

st.subheader("Risk Breakdown by Category")

category_df = calculate_category_scores(filtered_df)

fig = px.bar(
    category_df,
    x="risk_category",
    y="severity",
    color="company",
    barmode="group",
    title="Risk Distribution per Category"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Event Volume Over Time")

events_over_time = (
    filtered_df
    .groupby("event_date")
    .size()
    .reset_index(name="event_count")
)

fig_events = px.line(
    events_over_time,
    x="event_date",
    y="event_count",
    markers=True,
    title="Risk Events Over Time"
)

st.plotly_chart(fig_events, use_container_width=True)


st.subheader("Generated Alerts")

alerts = generate_alerts(scores, filtered_df)

if alerts:
    for alert in alerts:
        if alert["severity"] == "Critical":
            st.error(f'{alert["company"]}: {alert["message"]}')
        elif alert["severity"] == "High":
            st.warning(f'{alert["company"]}: {alert["message"]}')
        else:
            st.info(f'{alert["company"]}: {alert["message"]}')
else:
    st.success("No alerts generated.")


st.subheader("Risk Score Evolution")

score_timeline = calculate_score_over_time(filtered_df)

fig_score = px.line(
    score_timeline,
    x="event_date",
    y="risk_score",
    color="company",
    markers=True,
    title="Risk Score Evolution Over Time"
)

st.plotly_chart(fig_score, use_container_width=True)