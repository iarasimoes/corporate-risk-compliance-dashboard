def generate_alerts(scores, df):
    alerts = []

    for company, score in scores.items():
        company_events = df[df["company"] == company]

        critical_events = company_events[company_events["severity"] >= 5]
        recent_event_count = len(company_events)

        if score >= 75:
            alerts.append({
                "company": company,
                "severity": "Critical",
                "message": "High accumulated risk score detected."
            })

        elif score >= 55:
            alerts.append({
                "company": company,
                "severity": "High",
                "message": "Multiple relevant risk signals detected."
            })

        elif score >= 30:
            alerts.append({
                "company": company,
                "severity": "Attention",
                "message": "Early warning indicators are present."
            })

        if len(critical_events) >= 2:
            alerts.append({
                "company": company,
                "severity": "High",
                "message": "Multiple high-severity events detected."
            })

        if recent_event_count >= 3:
            alerts.append({
                "company": company,
                "severity": "Attention",
                "message": "Several risk events detected in the monitoring window."
            })

    return alerts