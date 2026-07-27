import os
import logging
import pandas as pd
from backend.agents.csv_agent import ingest_csv, eda_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ingest_csv_and_cleaning():
    # Path to your sample CSV in test_data
    csv_path = os.path.join("test_data", "bank_data.csv")

    df = ingest_csv(csv_path)

    # Logging for visibility
    logger.info("Cleaned DataFrame shape: %s", df.shape)
    logger.info("Columns after cleaning: %s", df.columns.tolist())

    # Basic validation
    assert df.shape[0] > 0
    assert isinstance(df.columns.tolist(), list)

def test_eda_summary():
    csv_path = os.path.join("test_data", "bank_data.csv")
    df = ingest_csv(csv_path)
    summary = eda_summary(df)

    # Log summary so you can see it in pytest output
    logger.info("EDA Summary: %s", summary)

    # Validation
    assert "shape" in summary
    assert "columns" in summary
    assert "missing_counts" in summary
    assert "sample" in summary