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

def calculate_score_over_time(df):
    records = []

    for company in df["company"].unique():
        company_df = df[df["company"] == company].sort_values("event_date")

        cumulative_score = 0

        for _, row in company_df.iterrows():
            category = row["risk_category"]
            severity = row["severity"]
            weight = WEIGHTS.get(category, 1)

            cumulative_score += severity * weight * 2
            cumulative_score = min(cumulative_score, 100)

            records.append({
                "company": company,
                "event_date": pd.to_datetime(row["event_date"]).date(),
                "risk_score": round(cumulative_score, 2)
            })

    result = pd.DataFrame(records)

    if not result.empty:
        result["event_date"] = pd.to_datetime(result["event_date"])

    return result