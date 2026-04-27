# Corporate Risk & Compliance Early Warning Dashboard

An interactive analytics dashboard designed to monitor public corporate signals that may indicate financial distress, governance failures, regulatory exposure, reputational deterioration, or systemic risk.

Built as a practical portfolio project combining **Data Analytics, Risk Monitoring, Compliance Concepts, Machine Learning, and Local AI (LLM)**.

---

## Project Overview

This project demonstrates how publicly available information can be transformed into an **Early Warning Monitoring System** for companies and sectors.

The objective is **not** to accuse, conclude wrongdoing, or replace financial/legal analysis.

Instead, it organizes weak and strong public signals into a structured analytical model that helps identify patterns of potential risk escalation.

---

## Why This Project Matters

Corporate crises rarely emerge from a single isolated event.

They often develop through combinations of signals such as:

- accounting inconsistencies  
- delayed reports  
- debt renegotiation  
- liquidity pressure  
- executive departures  
- regulatory investigations  
- reputational controversies  
- systemic financial stress  
- negative media concentration  

This project transforms those signals into measurable indicators and visual intelligence.

---

## Main Use Cases

- Corporate Risk Monitoring  
- Compliance Intelligence  
- Governance Analytics  
- Reputation Tracking  
- Financial Distress Monitoring  
- Banking / Systemic Risk Signals  
- Executive Dashboarding  
- Portfolio Demonstration

---

## Current Data Sources

Real public sources are currently used:

- Google News RSS  
- Public headlines / market news  
- Company-related public mentions

The historical dataset grows over time through automated collection.

---

## Risk Dimensions

The dashboard classifies events into explainable categories:

### Accounting Risk
Restatements, audit issues, irregularities, reporting concerns.

### Credit & Liquidity Risk
Debt pressure, refinancing stress, bankruptcy, cash constraints.

### Governance Risk
Board changes, CEO/CFO exits, conflicts, governance failures.

### Legal / Regulatory Risk
Investigations, lawsuits, regulators, fraud allegations.

### Reputational Risk
Scandals, controversies, media pressure, negative headlines.

### Financial System Risk
Central Bank intervention, FGC, liquidity crisis, contagion, solvency concerns.

---

## Risk Status Classification

| Score Range | Status |
|---|---|
| 0–29 | Normal |
| 30–54 | Attention |
| 55–74 | High Risk |
| 75–100 | Critical |

---

## Hybrid Intelligence Engine

This project combines **3 analytical layers**:

### 1. Rule-Based Risk Engine
Keyword taxonomy + sector-specific logic.

### 2. Machine Learning
TF-IDF + Logistic Regression classifier used as a secondary support signal.

### 3. Local AI (Ollama LLM)
Used for:

- News summarization  
- Contextual explanation  
- Explainability support

---

## Dashboard Tabs

### Overview
Executive KPIs, monitored companies, current risk exposure.

### Risk Analysis
Trends, categories, timeline, score evolution.

### Alerts
Generated alerts based on thresholds.

### Event Log
Detailed records of collected events.

### AI / ML Audit
Comparison between:

- rule-based classification  
- ML prediction  
- confidence levels  
- AI summaries

### About Project
Documentation, architecture and disclaimer.

---

## Technologies Used

### Python
Core language for ETL, scoring logic, automation and analytics.

### Streamlit
Rapid web dashboard development.

### Pandas
Data modeling, joins, transformations and time-series handling.

### Plotly
Interactive charts and executive visuals.

### Scikit-learn
Machine learning classifier for signal categorization.

### Ollama
Local LLM execution for AI summaries and explanations.

### GitHub
Version control and portfolio presentation.

### Linux VPS (Contabo)
Production hosting environment.

---

## Repository Structure

```bash
corporate-risk-compliance-dashboard/
│
├── app/
│   └── dashboard.py
│
├── data/
│   ├── mock/
│   ├── cache/
│   └── processed/
│
├── models/
│   └── signal_classifier.pkl
│
├── src/
│   ├── ai/
│   ├── ingestion/
│   ├── ml/
│   ├── processing/
│   └── scoring/
│
├── README.md
└── requirements.txt