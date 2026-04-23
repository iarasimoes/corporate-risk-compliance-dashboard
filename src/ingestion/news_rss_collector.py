import feedparser
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus


RISK_KEYWORDS = {
    "ACCOUNTING": ["accounting", "irregularity", "restatement", "financial statements", "audit"],
    "CREDIT_LIQUIDITY": ["debt", "liquidity", "creditor", "covenant", "bankruptcy", "restructuring"],
    "GOVERNANCE": ["CEO", "CFO", "board", "resignation", "executive"],
    "LEGAL_REGULATORY": ["investigation", "lawsuit", "regulator", "fraud", "probe"],
    "REPUTATIONAL": ["scandal", "controversy", "crisis", "allegation"],
}


def classify_news(text: str):
    text_lower = text.lower()
    matches = []

    for category, keywords in RISK_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches.append(category)
                break

    return matches[0] if matches else "GENERAL"


def collect_google_news(company_name: str, max_items: int = 10):
    query = quote_plus(f'"{company_name}" corporate risk OR debt OR investigation OR accounting')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(url)

    records = []

    for entry in feed.entries[:max_items]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        published = entry.get("published", "")

        text = f"{title} {summary}"
        category = classify_news(text)

        records.append({
            "company": company_name,
            "event_date": published or datetime.now().isoformat(),
            "event_type": "news_signal",
            "risk_category": category,
            "severity": 2 if category == "GENERAL" else 3,
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