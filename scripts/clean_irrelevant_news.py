from pathlib import Path
import pandas as pd

rules = {
    "Vale": ["port vale", "mclaren vale", "winery"],
    "Vivo": ["in vivo", "parkinson", "neurons", "biomarker"],
    "Stone": ["kidney stone", "renal", "urology", "uric acid"]
}

for file in Path("data/mock").glob("news_events*.csv"):
    try:
        df = pd.read_csv(file)
    except Exception:
        continue

    original_len = len(df)

    mask = []
    for _, row in df.iterrows():
        company = str(row.get("company", ""))
        text = str(row.get("description", "")).lower()

        is_irrelevant = company in rules and any(term in text for term in rules[company])
        mask.append(not is_irrelevant)

    cleaned_df = df[mask]
    cleaned_df.to_csv(file, index=False, encoding="utf-8-sig")

    print(f"{file}: removed {original_len - len(cleaned_df)} rows")