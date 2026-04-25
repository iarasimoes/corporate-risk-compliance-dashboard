import pandas as pd

WEIGHTS = {
    "ACCOUNTING": 1.2,
    "CREDIT_LIQUIDITY": 1.2,
    "GOVERNANCE": 1.0,
    "MARKET_STRESS": 0.8,
    "REPUTATIONAL": 0.8,
    "LEGAL_REGULATORY": 1.1,
    "FINANCIAL_SYSTEM_RISK": 1.3
}


def get_recency_factor(event_date):
    event_date = pd.to_datetime(event_date, errors="coerce")

    if pd.isna(event_date):
        return 0.5

    days = (pd.Timestamp.today() - event_date).days

    if days <= 30:
        return 1.0
    elif days <= 90:
        return 0.7
    elif days <= 180:
        return 0.4
    else:
        return 0.2


def calculate_score_over_time(df):
    records = []

    if df.empty:
        return pd.DataFrame(columns=["company", "event_date", "risk_score"])

    df = df.copy()
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    df["confidence_score"] = pd.to_numeric(
        df.get("confidence_score", 0.5),
        errors="coerce"
    ).fillna(0.5)

    for company in df["company"].dropna().unique():
        company_df = df[df["company"] == company].sort_values("event_date")

        cumulative_score = 0

        for _, row in company_df.iterrows():
            category = row.get("risk_category", "")
            severity = row.get("severity", 0)
            confidence = row.get("confidence_score", 0.5)
            weight = WEIGHTS.get(category, 1)
            recency = get_recency_factor(row.get("event_date"))

            cumulative_score += severity * weight * confidence * recency * 2
            cumulative_score = min(cumulative_score, 100)

            records.append({
                "company": company,
                "event_date": row["event_date"],
                "risk_score": round(cumulative_score, 2)
            })

    return pd.DataFrame(records)