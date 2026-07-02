from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/processed")


def read_csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path).fillna("")
