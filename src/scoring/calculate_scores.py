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


def recency_factor(date):
    days = (pd.Timestamp.today() - date).days

    if days <= 30:
        return 1.0
    elif days <= 90:
        return 0.7
    elif days <= 180:
        return 0.4
    else:
        return 0.2


def calculate_company_score(df):
    scores = {}

    for company in df['company'].unique():
        company_df = df[df['company'] == company]

        total_score = 0

        for _, row in company_df.iterrows():
            weight = WEIGHTS.get(row.get("risk_category", ""), 1)

            severity = row.get("severity", 0)

            confidence = row.get("confidence_score", 0.5)

            event_date = pd.to_datetime(row.get("event_date"), errors="coerce")

            if pd.isna(event_date):
                recency = 0.5
            else:
                recency = recency_factor(event_date)

            total_score += severity * weight * confidence * recency * 3

        total_score = min(total_score, 100)

        scores[company] = round(total_score, 2)

    return scores