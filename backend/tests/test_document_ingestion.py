import json

from backend.services.document_ingestion import DocumentIngestionService


def test_document_ingestion_service_reads_csv(tmp_path):
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text("order_id,status\nEC-1001,delayed\nEC-1002,delivered\n", encoding="utf-8")

    documents = DocumentIngestionService().ingest(str(csv_path))

    assert len(documents) == 2
    assert documents[0].metadata["file_type"] == "csv"
    assert "order_id: EC-1001" in documents[0].page_content


def test_document_ingestion_service_reads_json_object(tmp_path):
    json_path = tmp_path / "issue.json"
    json_path.write_text(json.dumps({"order_id": "EC-1042", "status": "refund_requested"}), encoding="utf-8")

    documents = DocumentIngestionService().ingest(str(json_path))

    assert documents
    assert documents[0].metadata["file_type"] == "json"
    assert "order_id: EC-1042" in documents[0].page_content


def test_document_ingestion_service_reads_json_list(tmp_path):
    json_path = tmp_path / "catalog.json"
    json_path.write_text(
        json.dumps(
            [
                {"sku": "SKU-1", "stock": 10},
                {"sku": "SKU-2", "stock": 0},
            ]
        ),
        encoding="utf-8",
    )

    documents = DocumentIngestionService().ingest(str(json_path))

    assert len(documents) == 2
    assert documents[1].metadata["file_type"] == "json"
    assert "sku: SKU-2" in documents[1].page_content
