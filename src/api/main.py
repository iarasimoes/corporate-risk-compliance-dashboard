from fastapi import FastAPI
from src.repository.csv_repository import read_csv
from src.services.company_service import get_companies, get_company_detail

app = FastAPI(
    title="Corporate Risk Intelligence API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "name": "Corporate Risk Intelligence API",
        "status": "running"
    }


@app.get("/summary")
def summary():
    df = read_csv("executive_risk_summary.csv")
    return df.to_dict(orient="records")


@app.get("/companies")
def companies():
    return get_companies()


@app.get("/company/{company_name}")
def company_detail(company_name: str):
    return get_company_detail(company_name)


@app.get("/events")
def events():
    df = read_csv("risk_events_clean.csv")
    return df.to_dict(orient="records")


@app.get("/alerts")
def alerts():
    df = read_csv("alerts_summary.csv")
    return df.to_dict(orient="records")