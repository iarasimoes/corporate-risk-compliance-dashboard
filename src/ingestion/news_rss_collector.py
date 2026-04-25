import feedparser
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus
from pathlib import Path
from datetime import datetime


RISK_KEYWORDS = {
    "ACCOUNTING": ["accounting", "irregularity", "restatement", "financial statements", "audit"],
    "CREDIT_LIQUIDITY": ["debt", "liquidity", "creditor", "covenant", "bankruptcy",\
    "restructuring", "funding", "capital structure",\
    "liquidez", "credor", "reestruturação", "captação"],
    "GOVERNANCE": ["CEO", "CFO", "board", "resignation", "executive"],
    "LEGAL_REGULATORY": ["investigation", "lawsuit", "regulator", "fraud", "probe"],
    "REPUTATIONAL": ["scandal", "controversy", "crisis", "allegation"],
    "FINANCIAL_SYSTEM_RISK": ["central bank", "banco central", "fgc", "deposit insurance",\
    "liquidation", "liquidação", "intervention", "intervenção",\
    "bank run", "liquidity crisis", "crise de liquidez",\
    "capital increase", "aumento de capital",\
    "subordinated debt", "dívida subordinada",\
    "asset sale", "venda de ativos",\
    "regulatory approval", "aprovação regulatória"],
}


def classify_news(text: str):
    text_lower = text.lower()

    matched = []
    category_scores = {}

    for category, keywords in RISK_KEYWORDS.items():
        matches = [kw for kw in keywords if kw.lower() in text_lower]

        if matches:
            matched.extend(matches)
            category_scores[category] = len(matches)

    if not category_scores:
        return {
            "risk_category": "GENERAL",
            "confidence_score": 0.1,
            "matched_keywords": [],
            "signal_type": "GENERAL_NEWS"
        }

    # categoria com mais matches
    best_category = max(category_scores, key=category_scores.get)
    total_matches = sum(category_scores.values())

    # confiança simples
    confidence = min(0.3 + (total_matches * 0.2), 1.0)

    # tipo de sinal
    if total_matches >= 3:
        signal_type = "CRITICAL_SIGNAL"
    elif total_matches == 2:
        signal_type = "RISK_SIGNAL"
    else:
        signal_type = "WEAK_SIGNAL"

    return {
        "risk_category": best_category,
        "confidence_score": round(confidence, 2),
        "matched_keywords": matched[:5],
        "signal_type": signal_type
    }


def collect_google_news(company_name: str, max_items: int = 10):
    query = quote_plus(
    	f'"{company_name}" '
    	f'(risco OR liquidez OR "Banco Central" OR FGC OR liquidação OR intervenção '
    	f'OR investigação OR dívida OR credores OR "aumento de capital" '
    	f'OR risk OR liquidity OR "central bank" OR liquidation OR creditors) '
   	 f'when:90d'
	)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(url)

    records = []

    for entry in feed.entries[:max_items]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        published = entry.get("published", None)

        if not published and hasattr(entry, "published_parsed"):
            published = datetime(*entry.published_parsed[:6]).isoformat()

        if not published:
            published = datetime.now().isoformat()

        text = f"{title} {summary}"
        classification = classify_news(text)

        category = classification["risk_category"]
        confidence = classification["confidence_score"]
        keywords = classification["matched_keywords"]
        signal_type = classification["signal_type"]

        records.append({
            "company": company_name,
            "event_date": published,
            "event_type": "news_signal",
            "risk_category": category,
            "severity": 2 if signal_type == "WEAK_SIGNAL" else (3 if signal_type == "RISK_SIGNAL" else 4),
            "confidence_score": confidence,
            "matched_keywords": ", ".join(keywords),
            "signal_type": signal_type,
            "description": title,
            "source_url": entry.get("link", ""),
            "source": "Google News RSS"
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    companies = ["Americanas SA", "Ambipar", "Enron"]

    all_news = []

    for company in companies:
        news_df = collect_google_news(company, max_items=10)
        all_news.append(news_df)

    final_df = pd.concat(all_news, ignore_index=True)
    final_df.to_csv("data/mock/news_events.csv", index=False, encoding="utf-8-sig")

    print("News RSS data saved to data/mock/news_events.csv")

def collect_all_news(companies=None):
    if companies is None:
        companies_df = pd.read_csv("data/mock/companies.csv")
        companies = companies_df["company"].dropna().unique().tolist()

    all_news = []

    for company in companies:
        news_df = collect_google_news(company, max_items=15)

        if not news_df.empty:
            all_news.append(news_df)

    if not all_news:
        return pd.DataFrame()

    new_df = pd.concat(all_news, ignore_index=True)

    new_df["collected_at"] = datetime.now().isoformat()

    history_path = Path("data/mock/news_events.csv")
    daily_path = Path(
        f"data/mock/news_events_{datetime.now().strftime('%Y%m%d')}.csv"
    )

    if history_path.exists() and history_path.stat().st_size > 0:
        try:
            history_df = pd.read_csv(history_path)
            final_df = pd.concat([history_df, new_df], ignore_index=True)
        except pd.errors.EmptyDataError:
            final_df = new_df
    else:
        final_df = new_df

    final_df = final_df.drop_duplicates(
        subset=["company", "source_url"],
        keep="last"
    )

    final_df.to_csv(history_path, index=False, encoding="utf-8-sig")
    new_df.to_csv(daily_path, index=False, encoding="utf-8-sig")

    return final_df