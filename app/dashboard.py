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

from src.dashboard.helpers import (
    get_status,
    get_dashboard_summary,
    calculate_category_scores,
    calculate_radar_scores,
    get_top_risk_drivers
)

st.set_page_config(
    page_title="Corporate Risk Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


def load_data():
    events_df = pd.read_csv("data/mock/events.csv")
    df = events_df

    news_files = sorted(Path("data/mock").glob("news_events*.csv"))
    news_dfs = []

    for news_file in news_files:
        try:
            if news_file.stat().st_size > 0:
                temp_df = pd.read_csv(news_file)

                if not temp_df.empty:
                    temp_df["source_file"] = news_file.name
                    news_dfs.append(temp_df)

        except pd.errors.EmptyDataError:
            continue

    if news_dfs:
        news_df = pd.concat(news_dfs, ignore_index=True)

        if "source_url" in news_df.columns:
            news_df = news_df.drop_duplicates(
                subset=["company", "source_url"],
                keep="last"
            )

        df = pd.concat([events_df, news_df], ignore_index=True)

    df["event_date"] = pd.to_datetime(
        df["event_date"],
        errors="coerce",
        utc=True
    ).dt.tz_convert(None)
    
    if "collected_at" in df.columns:
        df["collected_at"] = pd.to_datetime(
            df["collected_at"],
            errors="coerce",
            utc=True
        ).dt.tz_convert(None)
    else:
        df["collected_at"] = pd.NaT
    
    df["display_date"] = df["event_date"].fillna(df["collected_at"])
    df["event_day"] = df["display_date"].dt.date
    df["event_month"] = df["display_date"].dt.to_period("M").astype(str)
    df["severity"] = pd.to_numeric(df["severity"], errors="coerce").fillna(0)

    default_columns = {
        "confidence_score": 0.5,
        "matched_keywords": "",
        "signal_type": "MANUAL_EVENT",
        "source": "Manual/Mock",
        "source_url": ""
    }

    for col, default_value in default_columns.items():
        if col not in df.columns:
            df[col] = default_value

    df["confidence_score"] = pd.to_numeric(
        df["confidence_score"],
        errors="coerce"
    ).fillna(0.5)
    
    df = remove_irrelevant_news(df)
    
    return df

def remove_irrelevant_news(df):
    rules = {
        "Vale": ["port vale", "mclaren vale", "winery"],
        "Vivo": ["in vivo", "parkinson", "neurons", "biomarker"],
        "Stone": ["kidney stone", "renal", "urology", "uric acid"]
    }

    df = df.copy()
    keep_rows = []

    for _, row in df.iterrows():
        company = str(row.get("company", ""))
        text = str(row.get("description", "")).lower()

        if company in rules and any(term in text for term in rules[company]):
            keep_rows.append(False)
        else:
            keep_rows.append(True)

    return df[keep_rows]

st.title("📊 Corporate Risk & Compliance Dashboard")
st.caption("Monitoring public signals of corporate distress and risk escalation")

df = load_data()

    
try:
    companies_df = pd.read_csv("data/mock/companies.csv")
except FileNotFoundError:
    companies_df = pd.DataFrame({
        "company": df["company"].dropna().unique(),
        "sector": "Unknown"
    })

df = df.merge(
    companies_df[["company", "sector"]],
    on="company",
    how="left"
)

df["sector"] = df["sector"].fillna("Unknown")

st.subheader("🔎 Filters")

years_available = sorted(
    df["display_date"].dropna().dt.year.unique().tolist()
)

selected_years = st.multiselect(
    "Select Years",
    years_available,
    default=years_available
)

year_filtered_df = df[df["display_date"].dt.year.isin(selected_years)]

sector_options = sorted(
    companies_df["sector"].dropna().unique().tolist()
)

selected_sectors = st.multiselect(
    "Select Sector",
    sector_options,
    default=sector_options
)

company_options = sorted(
    companies_df[
        companies_df["sector"].isin(selected_sectors)
    ]["company"]
    .dropna()
    .unique()
    .tolist()
)

selected_companies = st.multiselect(
    "Select Companies",
    company_options,
    default=company_options
)

min_date = year_filtered_df["display_date"].min()
max_date = year_filtered_df["display_date"].max()

filter_col1, filter_col2 = st.columns([2, 1])

with filter_col1:
    selected_date_range = st.date_input(
        "Event Date Range",
        value=(min_date.date(), max_date.date())
    )

with filter_col2:
    st.markdown("### ")
    if st.button("🔄 Update News RSS"):
        with st.spinner("Fetching latest news..."):
            companies = companies_df["company"].dropna().unique().tolist()
            collect_all_news(companies)
        st.success("News updated.")
        st.rerun()

filtered_df = year_filtered_df[
    (year_filtered_df["sector"].isin(selected_sectors)) &
    (year_filtered_df["company"].isin(selected_companies))
]

if len(selected_date_range) == 2:
    start_date = pd.to_datetime(selected_date_range[0])
    end_date = pd.to_datetime(selected_date_range[1]) + pd.Timedelta(days=1)

    filtered_df = filtered_df[
        (filtered_df["display_date"] >= start_date) &
        (filtered_df["display_date"] < end_date)
    ]

if not selected_years or not selected_sectors or not selected_companies:
    st.warning("Please select at least one year, sector and company to display the dashboard.")
    st.stop()

scores = calculate_company_score(filtered_df)
alerts = generate_alerts(scores, filtered_df)
summary = get_dashboard_summary(filtered_df, scores, alerts)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "📈 Risk Analysis",
    "🚨 Alerts",
    "📋 Event Log",
    "🤖 AI/ML Audit",
    "ℹ️ About Project"
])

with tab1:
    st.subheader("📍 Executive Summary")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    kpi1.metric("Companies Monitored", summary["total_companies"])
    kpi2.metric("Risk Events", summary["total_events"])
    kpi3.metric("Average Risk Score", summary["avg_score"])
    kpi4.metric("Critical Alerts", summary["critical_alerts"])

    st.subheader("📌 Key Risk Indicators")
    
    if scores:
        score_items = list(scores.items())
        cards_per_row = 5
    
        for i in range(0, len(score_items), cards_per_row):
            row_items = score_items[i:i + cards_per_row]
            cols = st.columns(cards_per_row)
    
            for col, (company, score) in zip(cols, row_items):
                with col:
                    st.metric(
                        label=company,
                        value=f"{score}",
                        delta=get_status(score)
                    )
    else:
        st.info("No data available for the selected filter.")

    st.subheader("🏆 Highest Risk Companies")

    if scores:
        ranking_df = (
            pd.DataFrame([
                {"company": company, "risk_score": score, "status": get_status(score)}
                for company, score in scores.items()
            ])
            .sort_values("risk_score", ascending=False)
        )

        fig_ranking = px.bar(
            ranking_df,
            x="risk_score",
            y="company",
            orientation="h",
            text="risk_score",
            title="Companies Ranked by Risk Score"
        )

        fig_ranking.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=350
        )

        st.plotly_chart(fig_ranking, width="stretch")

        st.dataframe(
            ranking_df,
            width="stretch",
            height=250
        )
    else:
        st.info("No companies available for the selected filters.")

    st.subheader("🎯 Top Risk Drivers")

    drivers_df = get_top_risk_drivers(filtered_df)

    if not drivers_df.empty:
        for company in drivers_df["company"].unique():
            st.markdown(f"### {company}")

            company_drivers = drivers_df[drivers_df["company"] == company]

            for _, row in company_drivers.iterrows():
                st.markdown(
                    f"- **{row['risk_category']}** "
                    f"({row['signal_type']}) | "
                    f"Score: {round(row['event_score'], 2)}  \n"
                    f"{row.get('ai_summary', row['description'])}"
      
                )
                if "ai_explanation" in row:
                    st.caption(row["ai_explanation"])

            st.divider()
    else:
        st.info("No risk drivers available.")

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


with tab2:
    st.subheader("🔥 Sector Risk Heatmap")

    heatmap_df = (
        filtered_df
        .groupby(["sector", "risk_category"])["severity"]
        .sum()
        .reset_index()
    )

    if not heatmap_df.empty:
        heatmap_pivot = heatmap_df.pivot(
            index="sector",
            columns="risk_category",
            values="severity"
        ).fillna(0)

        fig_heatmap = px.imshow(
            heatmap_pivot,
            text_auto=True,
            aspect="auto",
            title="Risk Intensity by Sector and Category"
        )

        st.plotly_chart(fig_heatmap, width="stretch")
    else:
        st.info("No sector risk data available.")

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

            st.plotly_chart(fig_category, width="stretch")
        else:
            st.info("No category data available.")

    with col2:
        st.subheader("Event Volume Over Time")

        events_over_time = (
            filtered_df
            .dropna(subset=["display_date"])
            .assign(event_month=lambda x: x["display_date"].dt.to_period("M").dt.to_timestamp())
            .groupby("event_month")
            .size()
            .reset_index(name="event_count")
        )

        if not events_over_time.empty:
            fig_events = px.line(
                events_over_time,
                x="event_month",
                y="event_count",
                markers=True,
                title="Risk Events Over Time"
            )

            fig_events.update_xaxes(
                tickformat="%b %Y",
                dtick="M1"
            )

            st.plotly_chart(fig_events, width="stretch")
        else:
            st.info("No event timeline available.")

    st.subheader("🕸️ Risk Profile Radar")
    
    selected_company_radar = st.selectbox(
        "Select company for radar",
        sorted(filtered_df["company"].unique())
    )
    
    radar_df = category_df[
        category_df["company"] == selected_company_radar
    ].copy()
    
    radar_df["normalized"] = (
        radar_df["severity"] /
        radar_df["severity"].max()
    ) * 100
    
    fig = px.line_polar(
        radar_df,
        r="normalized",
        theta="risk_category",
        line_close=True
    )
    
    fig.update_traces(fill='toself')
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False
    )
    
    st.plotly_chart(fig, width="stretch")
        

    st.subheader("📈 Risk Score Evolution")

    score_timeline = calculate_score_over_time(filtered_df)
    
    if not score_timeline.empty:
        if "display_date" not in score_timeline.columns:
            if "event_date" in score_timeline.columns:
                score_timeline["display_date"] = score_timeline["event_date"]
            else:
                st.warning("Score timeline does not contain a valid date column.")
                st.stop()
    
        score_timeline["display_date"] = pd.to_datetime(
            score_timeline["display_date"],
            errors="coerce"
        )
    
        score_timeline["event_month"] = (
            score_timeline["display_date"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
    
        score_timeline = score_timeline.dropna(subset=["event_month"])
    
        score_timeline_monthly = (
            score_timeline
            .sort_values("display_date")
            .groupby(["company", "event_month"])
            .tail(1)
        )
    
        fig_score = px.line(
            score_timeline_monthly,
            x="event_month",
            y="risk_score",
            color="company",
            markers=True,
            title="Risk Score Evolution Over Time"
        )
    
        fig_score.update_xaxes(
            tickformat="%b %Y",
            dtick="M1"
        )
    
        st.plotly_chart(fig_score, width="stretch")
    else:
        st.info("No score evolution available.")


with tab3:
    st.subheader("🚨 Generated Alerts")

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


with tab4:
    st.subheader("📋 Event Log")

    event_log_columns = [
        "company",
        "sector",
        "event_date",
        "collected_at",
        "display_date",
        "risk_category",
        "signal_type",
        "severity",
        "confidence_score",
        "matched_keywords",
        "description",
        "ai_summary",
        "ai_explanation",
        "rule_signal_type",
        "final_signal_type",
        "ml_signal_type",
        "ml_confidence",
        "source",
        "source_url"
    ]
    
    available_columns = [
        col for col in event_log_columns
        if col in filtered_df.columns
    ]
    
    st.dataframe(
        filtered_df[available_columns].sort_values(
            by="display_date",
            ascending=False
        ),
        width="stretch",
        height=500
    )
    
with tab5:
    st.subheader("🤖 AI/ML Audit")
    
    st.info(
    """
    🤖 **Machine Learning Confidence Guide**
    
    - **0.85+** → Strong prediction  
    - **0.70 to 0.84** → Moderate confidence  
    - **Below 0.70** → Model still learning / limited historical patterns  
    
    The ML model is currently used as a supporting signal only and does not override the primary rule-based engine.
    """
    )

    audit_columns = [
        "company",
        "description",
        "risk_category",
        "rule_signal_type",
        "ml_signal_type",
        "ml_confidence",
        "final_signal_type",
        "confidence_score",
        "ai_summary",
        "ai_explanation",
        "source_url"
    ]

    available_audit_columns = [
        col for col in audit_columns
        if col in filtered_df.columns
    ]

    st.dataframe(
        filtered_df[available_audit_columns].sort_values(
            by="confidence_score",
            ascending=False
        ),
        width="stretch",
        height=500
    )
    
    if "ml_confidence" in filtered_df.columns:
        low_conf = filtered_df[
            filtered_df["ml_confidence"] < 0.70
        ]
    
        if len(low_conf) > 0:
            st.warning(
                f"{len(low_conf)} records have ML confidence below 0.70. "
                "This indicates the model may need more training data."
            )
            
with tab6:
    st.subheader("ℹ️ Corporate Risk & Compliance Dashboard")

    st.markdown("""
### 🎯 Project Objective

This project was developed as a practical study case focused on:

- Corporate risk monitoring  
- Early warning indicators  
- Public news signal detection  
- Compliance and governance analytics  
- Executive dashboarding for strategic visibility  

The purpose is to simulate how organizations may track public signals that could indicate financial distress, governance issues, legal exposure, reputational risk, or systemic concerns.

---

### 📅 Development Timeline

- **Project Start Date:** 24/04/2026

---

### 🔗 GitHub Repository

- https://github.com/iarasimoes/corporate-risk-compliance-dashboard

---

### 🛠️ Technologies Used (and Why)

#### Python
Used for data ingestion, automation, risk logic, machine learning and backend processing.

#### Streamlit
Rapid dashboard development with interactive filters and executive-style analytics.

#### Pandas
Data transformation, consolidation, time-series treatment and analysis.

#### Plotly
Interactive charts for risk trends, heatmaps and monitoring visuals.

#### Google News RSS
Public source used to capture market and corporate signals in near real-time.

#### Rule-Based Risk Engine
Custom logic to classify events into risk dimensions such as:

- Credit / Liquidity  
- Governance  
- Legal / Regulatory  
- Accounting  
- Reputational  
- Financial System Risk

#### Machine Learning (Scikit-learn)
Experimental classification model used as a secondary support signal.

#### Ollama / Local LLM
Used for AI-generated summaries and contextual explanations.

#### GitHub
Version control and portfolio showcase.

---

### ⚠️ Disclaimer

This dashboard was created exclusively for **educational, portfolio and study purposes**.

It must **not** be used as the sole basis for:

- Investment decisions  
- Credit analysis  
- Commercial approvals  
- Financial recommendations  
- Regulatory conclusions  
- Any real-world risk judgment

All data comes from public sources and automated interpretations that may contain inaccuracies, omissions, delays or classification errors.

Users should always perform independent validation before relying on any information.

---

### 👩‍💻 Author

Developed by **Iara Simões** as an applied analytics project combining:

- Data Analysis  
- Risk Monitoring  
- Compliance Concepts  
- Machine Learning  
- AI Applications  
- Dashboard Design
""")