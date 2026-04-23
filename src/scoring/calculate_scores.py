import pandas as pd

WEIGHTS = {
    "ACCOUNTING": 1.2,
    "CREDIT_LIQUIDITY": 1.2,
    "GOVERNANCE": 1.0,
    "MARKET_STRESS": 0.8,
    "REPUTATIONAL": 0.8,
    "LEGAL_REGULATORY": 1.1
}

def calculate_company_score(df):
    scores = {}

    for company in df['company'].unique():
        company_df = df[df['company'] == company]

        total_score = 0

        for _, row in company_df.iterrows():
            weight = WEIGHTS.get(row['risk_category'], 1)
            total_score += row['severity'] * weight

        total_score = min(total_score * 2, 100)
        scores[company] = round(total_score, 2)

    return scores