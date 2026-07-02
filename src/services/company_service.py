from src.repository.csv_repository import read_csv


def get_companies():
    df = read_csv("company_risk_scores.csv")
    return df.to_dict(orient="records")


def get_company_detail(company_name: str):
    scores_df = read_csv("company_risk_scores.csv")
    events_df = read_csv("risk_events_clean.csv")
    alerts_df = read_csv("alerts_summary.csv")

    company_score = scores_df[
        scores_df["company"].str.lower() == company_name.lower()
    ]

    company_events = events_df[
        events_df["company"].str.lower() == company_name.lower()
    ]

    company_alerts = alerts_df[
        alerts_df["company"].str.lower() == company_name.lower()
    ] if "company" in alerts_df.columns else alerts_df

    return {
        "profile": company_score.to_dict(orient="records")[0] if not company_score.empty else {},
        "alerts": company_alerts.to_dict(orient="records"),
        "latest_events": company_events.head(20).to_dict(orient="records"),
        "top_drivers": (
            company_events
            .sort_values("severity", ascending=False)
            .head(5)
            .to_dict(orient="records")
        ) if "severity" in company_events.columns else []
    }
