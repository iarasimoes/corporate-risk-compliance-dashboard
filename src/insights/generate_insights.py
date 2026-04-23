def generate_insights(df, scores):
    insights = {}

    for company in df["company"].unique():
        company_df = df[df["company"] == company]

        top_categories = (
            company_df.groupby("risk_category")["severity"]
            .sum()
            .sort_values(ascending=False)
        )

        main_categories = top_categories.head(3).index.tolist()

        events = company_df["event_type"].unique().tolist()

        explanation = f"Risk driven by {', '.join(main_categories)} signals."

        if len(events) > 0:
            explanation += f" Key events include: {', '.join(events[:3])}."

        score = scores.get(company, 0)

        if score >= 75:
            explanation += " Overall risk is critical."
        elif score >= 55:
            explanation += " Overall risk is high."
        elif score >= 30:
            explanation += " Early warning signals detected."
        else:
            explanation += " Risk level remains stable."

        insights[company] = explanation

    return insights