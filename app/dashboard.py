import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd
from src.scoring.calculate_scores import calculate_company_score
import plotly.express as px
from src.alerts.generate_alerts import generate_alerts

st.set_page_config(page_title="Corporate Risk Dashboard", layout="wide")

st.title("Corporate Risk & Compliance Dashboard")

df = pd.read_csv("data/mock/events.csv")
scores = calculate_company_score(df)

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

st.dataframe(df.sort_values(by="event_date", ascending=False))

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

st.subheader("Risk Breakdown by Category")

category_df = calculate_category_scores(df)

fig = px.bar(
    category_df,
    x="risk_category",
    y="severity",
    color="company",
    barmode="group",
    title="Risk Distribution per Category"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Generated Alerts")

alerts = generate_alerts(scores, df)

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