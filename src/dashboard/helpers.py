import pandas as pd


def get_status(score):
    if score < 30:
        return "🟢 Normal"
    elif score < 55:
        return "🟡 Attention"
    elif score < 75:
        return "🟠 High Risk"
    else:
        return "🔴 Critical"


def get_dashboard_summary(df, scores, alerts):
    total_companies = len(scores)
    total_events = len(df)
    avg_score = round(sum(scores.values()) / total_companies, 2) if total_companies else 0
    critical_alerts = len([a for a in alerts if a["severity"] == "Critical"])

    return {
        "total_companies": total_companies,
        "total_events": total_events,
        "avg_score": avg_score,
        "critical_alerts": critical_alerts
    }


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

    return (
        df.groupby(["company", "risk_category"])["severity"]
        .sum()
        .reset_index()
    )


def get_top_risk_drivers(df, top_n=3):
    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    if "confidence_score" not in df.columns:
        df["confidence_score"] = 0.5

    if "signal_type" not in df.columns:
        df["signal_type"] = "MANUAL_EVENT"

    df["event_score"] = df["severity"] * df["confidence_score"]

    drivers = (
        df
        .sort_values("event_score", ascending=False)
        .groupby("company")
        .head(top_n)
    )

    expected_cols = [
        "company",
        "event_date",
        "risk_category",
        "signal_type",
        "event_score",
        "description"
    ]

    return drivers[[col for col in expected_cols if col in drivers.columns]]