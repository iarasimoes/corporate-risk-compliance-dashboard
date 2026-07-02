from pathlib import Path
import json
import pandas as pd

# limpa CSVs
for file in Path("data/mock").glob("news_events*.csv"):
    try:
        df = pd.read_csv(file)
    except Exception:
        continue

    for col in ["ai_summary", "ai_explanation"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
            df.loc[df[col].astype(str).str.startswith("Error:"), col] = ""

    df.to_csv(file, index=False, encoding="utf-8-sig")
    print(f"Cleaned CSV: {file}")

# limpa cache
cache_file = Path("data/cache/ai_news_cache.json")

if cache_file.exists():
    with open(cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)

    for _, item in cache.items():
        for col in ["ai_summary", "ai_explanation"]:
            if str(item.get(col, "")).startswith("Error:"):
                item[col] = ""

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print("Cleaned AI cache")