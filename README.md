# Corporate Risk & Compliance Early Warning Dashboard

A web-based dashboard for monitoring public signals of corporate distress, governance issues, compliance risk, and reputational deterioration using explainable indicators.

## Project Overview

This project aims to demonstrate how public data can be transformed into an early-warning monitoring system for corporate risk analysis.

The dashboard does **not** detect fraud, determine guilt, or replace legal, audit, or investment analysis. Its purpose is to organize public signals into a structured analytical framework that helps identify patterns of risk escalation.

## Why This Project Matters

Corporate crises rarely appear from a single isolated event. They often emerge through a combination of weak signals, such as:

- accounting inconsistencies;
- delayed financial reports;
- debt renegotiation;
- executive departures;
- legal or regulatory investigations;
- negative media spikes;
- abnormal market volatility;
- reputational deterioration.

This project turns those signals into measurable indicators and visual alerts.

## Main Use Cases

- Risk monitoring
- Compliance intelligence
- Governance analysis
- Reputation tracking
- Financial distress monitoring
- Data analytics portfolio demonstration

## Risk Dimensions

The dashboard is structured around five main risk dimensions:

### 1. Accounting Risk
Signals related to financial reporting, inconsistencies, restatements, auditor changes, delayed filings, or accounting-related controversies.

### 2. Credit & Liquidity Risk
Signals related to debt pressure, renegotiation, covenant issues, liquidity stress, bankruptcy protection, or severe financial constraints.

### 3. Governance Risk
Signals related to executive departures, board changes, investigations, conflicts of interest, or governance failures.

### 4. Market Stress Risk
Signals related to abnormal stock price movement, volume spikes, volatility increases, or sudden investor reaction.

### 5. Reputational Risk
Signals related to negative news concentration, public scrutiny, repeated critical keywords, or media sentiment deterioration.

## Risk Score Methodology

The project uses an explainable score from 0 to 100.

```text
Total Risk Score =
25% Accounting Risk +
25% Credit & Liquidity Risk +
20% Governance Risk +
15% Market Stress Risk +
15% Reputational Risk
```

## Risk Status Classification

| Score Range | Status |
|---|---|
| 0–29 | Normal |
| 30–54 | Attention |
| 55–74 | High Risk |
| 75–100 | Critical |

## Dashboard Pages

### 1. Overview
Executive view with monitored companies, current risk score, active alerts, and score evolution.

### 2. Company Detail
Detailed company-level analysis with risk dimensions, timeline of events, recent signals, and alert explanation.

### 3. Alerts
List of generated alerts with severity, trigger reason, company, and date.

### 4. Methodology
Explanation of the scoring logic, risk taxonomy, limitations, and ethical considerations.

## Initial Data Strategy

The first version uses mock data inspired by common corporate crisis patterns. This allows the project to focus on modeling, scoring, dashboard design, and documentation before connecting to real public data sources.

Example fictional companies:

- Alpha Retail — accounting risk pattern
- Vertex Energy — credit and liquidity stress pattern
- Nova Environmental — governance and reputational risk pattern

## Future Data Sources

Potential public data sources for future versions:

- Google News RSS
- company investor relations pages
- public regulatory filings
- market data APIs
- public corporate announcements
- financial news portals

## Planned Features

### V1
- mock event dataset;
- explainable risk taxonomy;
- risk score calculation;
- alert generation;
- Streamlit dashboard;
- GitHub documentation.

### V2
- public news ingestion;
- market data integration;
- automated scheduled updates;
- PostgreSQL storage;
- deployment on a VPS;
- portfolio integration.

### V3
- AI-assisted event classification;
- news summarization;
- entity extraction;
- alert explanation generation;
- API layer using FastAPI.

## Ethical Disclaimer

This project uses public information and simulated data for educational and analytical purposes. It does not accuse any company or individual of wrongdoing and should not be used as legal, audit, investment, or financial advice.

The goal is to demonstrate how data analytics can support structured monitoring of public risk signals.

## Tech Stack

Initial version:

- Python
- Streamlit
- SQLite or CSV files
- Plotly
- GitHub

Future version:

- FastAPI
- PostgreSQL
- Docker
- Nginx
- scheduled data pipelines
- AI-assisted classification

## Repository Structure

```bash
corporate-risk-compliance-dashboard/
│
├── app/
│   └── dashboard.py
│
├── data/
│   ├── mock/
│   └── processed/
│
├── src/
│   ├── ingestion/
│   ├── processing/
│   ├── scoring/
│   └── database/
│
├── sql/
│   └── schema.sql
│
├── docs/
│   ├── methodology.md
│   ├── risk_taxonomy.md
│   └── limitations.md
│
├── README.md
├── requirements.txt
└── .env.example
```

## Portfolio Positioning

This project demonstrates:

- data modeling;
- business-oriented analytics;
- compliance and governance thinking;
- risk indicator design;
- dashboard development;
- automation potential;
- responsible use of public data.

