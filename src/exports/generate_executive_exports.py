from pathlib import Path
import pandas as pd

from src.scoring.calculate_scores import calculate_company_score
from src.alerts.generate_alerts import generate_alerts


DATA_DIR = Path("data/mock")
OUTPUT_DIR = Path("data/processed")


def get_status(score):
    if score < 30:
        return "Normal"
    elif score < 55:
        return "Attention"
    elif score < 75:
        return "High Risk"
    return "Critical"


def load_events():
    events_df = pd.read_csv(DATA_DIR / "events.csv")

    news_files = sorted(DATA_DIR.glob("news_events*.csv"))
    news_dfs = []

    for file in news_files:
        try:
            if file.stat().st_size > 0:
                temp_df = pd.read_csv(file)
                if not temp_df.empty:
                    news_dfs.append(temp_df)
        except Exception:
            continue

    if news_dfs:
        news_df = pd.concat(news_dfs, ignore_index=True)

        if "source_url" in news_df.columns:
            news_df = news_df.drop_duplicates(
                subset=["company", "source_url"],
                keep="last"
            )

        df = pd.concat([events_df, news_df], ignore_index=True)
    else:
        df = events_df

    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce", utc=True).dt.tz_convert(None)

    if "collected_at" in df.columns:
        df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce", utc=True).dt.tz_convert(None)
    else:
        df["collected_at"] = pd.NaT

    df["display_date"] = df["event_date"].fillna(df["collected_at"])
    df["severity"] = pd.to_numeric(df["severity"], errors="coerce").fillna(0)
    df["confidence_score"] = pd.to_numeric(
        df.get("confidence_score", 0.5),
        errors="coerce"
    ).fillna(0.5)

    default_columns = {
        "risk_category": "GENERAL",
        "signal_type": "GENERAL_NEWS",
        "final_signal_type": "",
        "ml_signal_type": "",
        "ml_confidence": "",
        "ai_summary": "",
        "ai_explanation": "",
        "source_url": "",
        "source": ""
    }

    for col, default_value in default_columns.items():
        if col not in df.columns:
            df[col] = default_value

    try:
        companies_df = pd.read_csv(DATA_DIR / "companies.csv")
        df = df.merge(
            companies_df[["company", "sector"]],
            on="company",
            how="left"
        )
        df["sector"] = df["sector"].fillna("Unknown")
    except Exception:
        df["sector"] = "Unknown"

    return df


def export_risk_events_clean(df):
    columns = [
        "company",
        "sector",
        "display_date",
        "event_date",
        "collected_at",
        "risk_category",
        "signal_type",
        "final_signal_type",
        "severity",
        "confidence_score",
        "ml_signal_type",
        "ml_confidence",
        "description",
        "ai_summary",
        "ai_explanation",
        "source",
        "source_url"
    ]

    available = [col for col in columns if col in df.columns]

    output = df[available].sort_values("display_date", ascending=False)

    output.to_csv(
        OUTPUT_DIR / "risk_events_clean.csv",
        index=False,
        encoding="utf-8-sig"
    )

    return output


def export_company_risk_scores(df):
    scores = calculate_company_score(df)

    rows = []

    for company, score in scores.items():
        company_df = df[df["company"] == company]

        top_category = (
            company_df.groupby("risk_category")["severity"]
            .sum()
            .sort_values(ascending=False)
        )

        rows.append({
            "company": company,
            "sector": company_df["sector"].dropna().iloc[0] if not company_df.empty else "Unknown",
            "risk_score": score,
            "status": get_status(score),
            "total_events": len(company_df),
            "critical_signals": len(company_df[company_df["signal_type"] == "CRITICAL_SIGNAL"]),
            "risk_signals": len(company_df[company_df["signal_type"] == "RISK_SIGNAL"]),
            "last_event_date": company_df["display_date"].max(),
            "top_risk_category": top_category.index[0] if len(top_category) > 0 else "GENERAL"
        })

    output = pd.DataFrame(rows).sort_values("risk_score", ascending=False)

    output.to_csv(
        OUTPUT_DIR / "company_risk_scores.csv",
        index=False,
        encoding="utf-8-sig"
    )

    return output


def export_alerts_summary(df):
    scores = calculate_company_score(df)
    alerts = generate_alerts(scores, df)

    output = pd.DataFrame(alerts)

    if not output.empty:
        output["generated_at"] = pd.Timestamp.now()
        output.to_csv(
            OUTPUT_DIR / "alerts_summary.csv",
            index=False,
            encoding="utf-8-sig"
        )
    else:
        output = pd.DataFrame(columns=[
            "company",
            "severity",
            "message",
            "generated_at"
        ])
        output.to_csv(
            OUTPUT_DIR / "alerts_summary.csv",
            index=False,
            encoding="utf-8-sig"
        )

    return output


def export_executive_summary(df, company_scores):
    output = pd.DataFrame([{
        "total_companies": company_scores["company"].nunique() if not company_scores.empty else 0,
        "total_events": len(df),
        "companies_attention_or_above": len(company_scores[company_scores["risk_score"] >= 30]) if not company_scores.empty else 0,
        "companies_high_or_critical": len(company_scores[company_scores["risk_score"] >= 55]) if not company_scores.empty else 0,
        "companies_critical": len(company_scores[company_scores["risk_score"] >= 75]) if not company_scores.empty else 0,
        "last_update": pd.Timestamp.now(),
        "last_event_date": df["display_date"].max()
    }])

    output.to_csv(
        OUTPUT_DIR / "executive_risk_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    return output


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_events()

    risk_events = export_risk_events_clean(df)
    company_scores = export_company_risk_scores(df)
    alerts = export_alerts_summary(df)
    executive_summary = export_executive_summary(df, company_scores)

    print("Executive exports generated:")
    print(f"- {OUTPUT_DIR / 'risk_events_clean.csv'} ({len(risk_events)} rows)")
    print(f"- {OUTPUT_DIR / 'company_risk_scores.csv'} ({len(company_scores)} rows)")
    print(f"- {OUTPUT_DIR / 'alerts_summary.csv'} ({len(alerts)} rows)")
    print(f"- {OUTPUT_DIR / 'executive_risk_summary.csv'}")


if __name__ == "__main__":
    main()