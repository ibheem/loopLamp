import pandas as pd

from backend.services.document_ingestion import ingest_csv

def eda_summary(df: pd.DataFrame):
    summary = {
        "shape": df.shape,
        "columns": list(df.columns),
        "missing_counts": df.isnull().sum().to_dict(),
        "sample": df.head(5).to_dict(orient="records"),
    }
    return summary
