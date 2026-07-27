import pandas as pd

def ingest_csv(path: str):
    """
    Load and clean CSV data for downstream use.
    """
    df = pd.read_csv(path)

    # Basic cleaning
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.drop_duplicates()

    # Handle missing values (simple strategy)
    df = df.fillna("N/A")

    return df

def eda_summary(df: pd.DataFrame):
    """
    Generate quick EDA summary for inspection.
    """
    summary = {
        "shape": df.shape,
        "columns": list(df.columns),
        "missing_counts": df.isnull().sum().to_dict(),
        "sample": df.head(5).to_dict(orient="records")
    }
    return summary
