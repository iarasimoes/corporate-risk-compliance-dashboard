import feedparser
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus
from pathlib import Path
from src.ai.ollama_client import summarize_news, explain_risk
from src.ml.predict_signal import predict_signal_type
import json
import hashlib


RISK_KEYWORDS = {
    "ACCOUNTING": [
        "accounting", "irregularity", "restatement",
        "financial statements", "audit"
    ],
    "CREDIT_LIQUIDITY": [
        "debt", "liquidity", "creditor", "creditors", "covenant",
        "bankruptcy", "restructuring", "funding", "capital structure",
        "default", "missed payment", "debt maturity",
        "refinancing", "cash crunch", "cash flow pressure",
        "liquidez", "credor", "credores", "reestruturação", "captação",
        "inadimplência", "calote", "vencimento de dívida",
        "rolagem de dívida", "pressão de caixa",
        "dívida", "endividamento", "alavancagem",
        "risco de crédito", "crédito problemático"
    ],
    "GOVERNANCE": [
        "CEO", "CFO", "board", "resignation", "executive"
    ],
    "LEGAL_REGULATORY": [
        "investigation", "lawsuit", "regulator", "fraud", "probe"
    ],
    "REPUTATIONAL": [
        "scandal", "controversy", "crisis", "allegation"
    ],
    "FINANCIAL_SYSTEM_RISK": [
        "central bank", "banco central", "bacen", "bc",
        "fgc", "fundo garantidor de créditos", "deposit insurance",
        "liquidation", "liquidação", "liquidado", "liquidada",
        "extraordinary liquidation", "liquidação extrajudicial",
        "intervention", "intervenção", "intervenção extrajudicial",
        "bank run", "corrida bancária",
        "liquidity crisis", "crise de liquidez", "stress de liquidez",
        "capital increase", "aumento de capital",
        "subordinated debt", "dívida subordinada",
        "asset sale", "venda de ativos", "carteira de crédito",
        "regulatory approval", "aprovação regulatória",
        "regulatory risk", "risco regulatório",
        "contagion", "contágio",
        "prudential", "prudencial",
        "solvency", "solvência",
        "insolvency", "insolvência",
        "intervenor", "interventor",
        "resolution regime", "regime de resolução",
        "judicial recovery", "recuperação judicial",
        "bankruptcy protection", "proteção contra falência",
        "special temporary administration", "administração especial temporária",
        "raet",
        "operational error", "erro operacional",
        "false message", "mensagem indevida",
        "wrong notification", "mistaken notification",
        "push notification", "notification"
    ],
}


AI_CACHE_PATH = Path("data/cache/ai_news_cache.json")


def get_query_name(company_name, aliases="", ticker=""):
    custom = {
        "Vivo": '"Telefônica Brasil" OR "Telefonica Brasil" OR VIVT3 OR "Vivo telecom"',
        "Stone": '"StoneCo" OR STNE OR "Stone payments"',
        "Vale": '"Vale SA" OR "Vale S.A." OR VALE3 OR "Vale mining"',
        "Oi": '"Oi SA" OR "Oi S.A." OR OIBR3 OR "Oi telecom"',
        "Banco Inter": '"Banco Inter" OR INBR32',
        "PagBank": '"PagBank" OR PagSeguro OR PAGS',
        "Nubank": '"Nubank" OR "Nu Holdings" OR "Nubank Brasil" OR "NYSE: NU"',
        "XP Inc": '"XP Inc" OR "XP Investimentos" OR "NASDAQ: XP" OR "XP stock"'
    }

    if company_name in custom:
        return custom[company_name]

    alias_list = []

    if aliases and not pd.isna(aliases):
        alias_list = [
            f'"{a.strip()}"'
            for a in str(aliases).split("|")
            if a.strip()
        ]

    if ticker and not pd.isna(ticker):
        ticker_clean = str(ticker).replace(".SA", "").strip()
        if ticker_clean:
            alias_list.append(ticker_clean)

    if alias_list:
        return " OR ".join(alias_list[:4])

    return f'"{company_name}"'


def is_relevant_to_company(company_name, text, company_aliases=None):
    text_lower = str(text).lower()
    company_lower = str(company_name).lower()

    irrelevant_terms_by_company = {
        "XP Inc": [
            "windows xp",
            "microsoft xp",
            "windows operating system",
            "windows nostalgia"
        ],
        "Nubank": [
            "nu.edu",
            "national university",
            "northwestern university",
            "alani nu",
            "nu medicine",
            "nu-world",
            "nu e power"
        ],
        "Stone": [
            "kidney stone",
            "urinary stone",
            "renal stone",
            "gallstone"
        ],
        "Vivo": [
            "in vivo",
            "ex vivo",
            "vivo x",
            "vivo phone",
            "vivo smartphone"
        ],
        "Vale": [
            "port vale",
            "mclaren vale",
            "vale winery"
        ]
    }

    if company_name in irrelevant_terms_by_company:
        if any(term in text_lower for term in irrelevant_terms_by_company[company_name]):
            return False

    aliases = []

    if company_aliases and not pd.isna(company_aliases):
        aliases = [
            alias.strip().lower()
            for alias in str(company_aliases).split("|")
            if alias.strip()
        ]

    search_terms = [company_lower] + aliases

    if any(term in text_lower for term in search_terms):
        return True

    fallback_terms = {
        "Nubank": ["nu holdings", "nubank brasil", "nyse: nu"],
        "XP Inc": ["xp investimentos", "xp inc", "nasdaq: xp"],
        "Stone": ["stoneco", "stne"],
        "Vivo": ["telefônica brasil", "telefonica brasil", "vivt3"],
        "Vale": ["vale sa", "vale s.a.", "vale3"],
        "Oi": ["oi sa", "oi s.a.", "oibr3"],
        "BRB Banco de Brasília": ["brb", "banco de brasília", "banco de brasilia"]
    }

    for term in fallback_terms.get(company_name, []):
        if term in text_lower:
            return True

    return False


def apply_sector_specific_rules(company_name, text, category, signal_type, confidence):
    text_lower = str(text).lower()
    company_lower = str(company_name).lower()

    critical_terms = [
        "liquidação extrajudicial",
        "banco central",
        "fgc",
        "intervenção",
        "liquidation",
        "central bank",
        "bankruptcy",
        "insolvency",
        "fraud",
        "investigation"
    ]

    yellow_terms = [
        "brb",
        "banco de brasília",
        "assets linked",
        "linked to banco master",
        "venda de ativos",
        "carteira",
        "capital increase",
        "aumento de capital",
        "regulatory approval",
        "risco regulatório"
    ]

    nubank_terms = [
        "liquidação extrajudicial",
        "liquidation",
        "banco central",
        "central bank",
        "fgc",
        "erro operacional",
        "operational error",
        "mensagem indevida",
        "false message",
        "wrong notification",
        "mistaken notification",
        "notification",
        "push notification",
        "email",
        "e-mail"
    ]

    if "banco master" in company_lower:
        if any(term in text_lower for term in critical_terms):
            return "FINANCIAL_SYSTEM_RISK", "CRITICAL_SIGNAL", max(confidence, 0.9)

    if "brb" in company_lower or "banco de brasília" in company_lower:
        if any(term in text_lower for term in yellow_terms + critical_terms):
            return "FINANCIAL_SYSTEM_RISK", "RISK_SIGNAL", max(confidence, 0.65)

    if "nubank" in company_lower:
        if any(term in text_lower for term in nubank_terms):
            return "FINANCIAL_SYSTEM_RISK", "RISK_SIGNAL", max(confidence, 0.75)

    return category, signal_type, confidence


def load_ai_cache():
    if AI_CACHE_PATH.exists():
        try:
            with open(AI_CACHE_PATH, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}


def save_ai_cache(cache):
    AI_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(AI_CACHE_PATH, "w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False, indent=2)


def build_cache_key(company, title, source_url):
    raw_key = f"{company}|{title}|{source_url}"
    return hashlib.md5(raw_key.encode("utf-8")).hexdigest()


def get_ai_enrichment(company, title, source_url, signal_type):
    cache = load_ai_cache()
    cache_key = build_cache_key(company, title, source_url)

    cached = cache.get(cache_key)

    if cached and (
        cached.get("ai_summary") or cached.get("ai_explanation")
    ):
        return cached

    empty_result = {
        "ai_summary": "",
        "ai_explanation": ""
    }

    if signal_type not in ["RISK_SIGNAL", "CRITICAL_SIGNAL"]:
        return empty_result

    try:
        ai_summary = summarize_news(title)
        ai_explanation = explain_risk(title)

        ai_result = {
            "ai_summary": ai_summary or "",
            "ai_explanation": ai_explanation or ""
        }

        # não salva erro nem resposta vazia no cache
        if (
            ai_result["ai_summary"].startswith("Error:")
            or ai_result["ai_explanation"].startswith("Error:")
            or not ai_result["ai_summary"]
            or not ai_result["ai_explanation"]
        ):
            return empty_result

        cache[cache_key] = ai_result
        save_ai_cache(cache)

        return ai_result

    except Exception as e:
        print(f"Ollama error for {company}: {e}")
        return empty_result


def classify_news(text: str):
    text_lower = str(text).lower()

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

    best_category = max(category_scores, key=category_scores.get)
    total_matches = sum(category_scores.values())

    confidence = min(0.3 + (total_matches * 0.2), 1.0)

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


def collect_google_news(company_name, max_items=10, company_aliases=None, ticker=None):
    query_name = get_query_name(company_name, company_aliases, ticker)

    query = quote_plus(
        f'({query_name}) '
        f'(risco OR liquidez OR "Banco Central" OR FGC '
        f'OR liquidação OR intervenção '
        f'OR investigação OR dívida OR credores '
        f'OR "aumento de capital" '
        f'OR "erro operacional" '
        f'OR "mensagem indevida" '
        f'OR notificação '
        f'OR email '
        f'OR e-mail '
        f'OR "liquidação extrajudicial" '
        f'OR notification '
        f'OR "push notification" '
        f'OR "false message" '
        f'OR "wrong notification" '
        f'OR "mistaken notification" '
        f'OR risk OR liquidity OR "central bank" '
        f'OR liquidation OR creditors '
        f'OR earnings OR results OR shares OR stock OR dividend) '
        f'when:90d'
    )

    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(url)

    records = []

    for entry in feed.entries[:max_items]:
        title = entry.get("title", "")
        news_summary = entry.get("summary", "")
        source_url = entry.get("link", "")
        text = f"{title} {news_summary}"

        if not is_relevant_to_company(company_name, text, company_aliases):
            continue

        published = None

        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime(*entry.published_parsed[:6])
            except Exception:
                published = None

        elif entry.get("published"):
            try:
                published = pd.to_datetime(entry.get("published"), errors="coerce")
            except Exception:
                published = None

        event_date = published
        collected_at = datetime.now()

        classification = classify_news(text)

        category = classification["risk_category"]
        confidence = classification["confidence_score"]
        keywords = classification["matched_keywords"]
        signal_type = classification["signal_type"]

        category, signal_type, confidence = apply_sector_specific_rules(
            company_name=company_name,
            text=text,
            category=category,
            signal_type=signal_type,
            confidence=confidence
        )

        ml_signal_type, ml_confidence = predict_signal_type(
            description=title,
            matched_keywords=", ".join(keywords),
        )

        rule_signal_type = signal_type
        final_signal_type = signal_type

        if ml_signal_type:
            if ml_signal_type == signal_type:
                confidence = min(confidence + 0.1, 1.0)
                final_signal_type = signal_type
            elif ml_confidence and ml_confidence >= 0.75:
                final_signal_type = ml_signal_type
                confidence = max(confidence, ml_confidence)

        try:
            ai_result = get_ai_enrichment(
                company=company_name,
                title=title,
                source_url=source_url,
                signal_type=signal_type
            )

            ai_summary = ai_result["ai_summary"]
            ai_explanation = ai_result["ai_explanation"]
        except Exception:
            ai_summary = ""
            ai_explanation = ""

        records.append({
            "company": company_name,
            "event_date": event_date,
            "collected_at": collected_at,
            "event_type": "news_signal",
            "risk_category": category,
            "severity": (
                5 if final_signal_type == "CRITICAL_SIGNAL"
                else 4 if final_signal_type == "RISK_SIGNAL"
                else 2 if final_signal_type == "WEAK_SIGNAL"
                else 1
            ),
            "confidence_score": confidence,
            "matched_keywords": ", ".join(keywords),
            "signal_type": signal_type,
            "rule_signal_type": rule_signal_type,
            "final_signal_type": final_signal_type,
            "ml_signal_type": ml_signal_type,
            "ml_confidence": ml_confidence,
            "description": title,
            "source_url": source_url,
            "source": "Google News RSS",
            "ai_summary": ai_summary,
            "ai_explanation": ai_explanation,
        })

    return pd.DataFrame(records)


def collect_all_news(companies=None):
    companies_df = pd.read_csv("data/mock/companies.csv")

    if companies is None:
        selected_df = companies_df.copy()
    else:
        selected_df = companies_df[
            companies_df["company"].isin(companies)
        ]

    all_news = []

    for _, row in selected_df.iterrows():
        company = row["company"]
        aliases = row.get("aliases", "")
        ticker = row.get("ticker", "")

        news_df = collect_google_news(
            company_name=company,
            max_items=15,
            company_aliases=aliases,
            ticker=ticker
        )

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


if __name__ == "__main__":
    result_df = collect_all_news()
    print(f"News collection completed. {len(result_df)} records available in history.")